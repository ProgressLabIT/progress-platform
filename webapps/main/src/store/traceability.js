import Vue from 'vue'
import { api } from '@/lib/apiCall.js'
import { DateTime as DT } from 'luxon'


function createWorkSession(state, startDT) {
  const job_id = state.working_job_data._id
  const user_id = state.user._id
  const user_session_id = state.user_session._id
  
  const ws_start = startDT.toISO()
  
  return {
    start: ws_start,
    user_session_id,
    user_id,
    job_id,
    active: true
  }
}

function createBatch(state, startDT) {
  const job = state.working_job_data
  const job_id = job._id
  const new_batch = {
    job_id,
    start: startDT.toISO(),
  }

  const procedure = state.working_job_data.step_sequence
  if (procedure.length) new_batch.procedure = procedure.map( step => {
    return {
      _id: step._id,
      done: false,
      critical: false,
      user_data: []
    }
  })

  return new_batch
}

function getClosedWorkSessionData(state, endDT) {
  const ws_list_length = state.work_session_list.length
  const current_work_session = state.work_session_list[ws_list_length-1]

  const updated_work_session = {
    ...current_work_session,
    end: endDT.toISO(),
    active: false
  }
  return updated_work_session
}



const traceability = {

  state: {
    user: {
      name: 'Cristian',
      surname: 'Colombara',
      _id: 'User/12005330'
    },
    user_session: {
      _id: 'UserSession/123456',
      _key: '123456'
    },
    permissions: null,
    working_job_data: {},
    work_session_list: [],
    current_batch_data: {},
  },

  getters: {
    getBatchStep: state => step_id => {
      const batch_procedure = state.current_batch_data.procedure
      if (batch_procedure) {
        const batch_step = batch_procedure.find( step => step._id === step_id )
        return batch_step
      }
      else return {}
    }
  },

  mutations: {

    START_USER_SESSION(state, session_data) {
      Vue.set(state, 'user', session_data)
    },

    LOAD_WORKING_JOB_DATA(state, job_data) {
      Vue.set(state, 'working_job_data', job_data)
    },

    START_JOB(state, {new_work_session, new_batch, updated_job_data}) {
      // get timestamp and state metadata
      state.work_session_list.push(new_work_session)
      Vue.set(state, 'current_batch_data', new_batch)
      Vue.set(state, 'working_job_data', updated_job_data)
    },

    CLOSE_WORK_SESSION(state, updated_work_session) {
      // Update general list of work sessions
      const ws_list_length = state.work_session_list.length
      Vue.set(state.work_session_list, ws_list_length-1, updated_work_session)

      // Update Job status
      Vue.set(state.working_job_data, 'active', false)
    },

    RESUME_JOB(state, new_work_session) {
      // Add work session to list
      state.work_session_list.push(new_work_session)      
      Vue.set(state.working_job_data, 'active', true)
      Vue.set(state.working_job_data, 'last_work_session_started', new_work_session._key)
    },

    COMPLETE_STEP(state, step_index) {
      Vue.set(state.current_batch_data.procedure[step_index], 'done', true)
    },

    UPDATE_USER_DATA(state, { step_id, value_index, value }) {
      const batch_data = state.current_batch_data
      const step_data = batch_data.procedure.find( step => step._id === step_id )
      Vue.set(step_data.user_data, value_index, value)
    },

    COMPLETE_BATCH(state, { qt_completed, new_batch }) {
      Vue.set(state.working_job_data, 'qt_completed', qt_completed)
      Vue.set(state, 'current_batch_data', new_batch)
    },

    COMPLETE_JOB(state, endDT) {
      const job = state.working_job_data
      const updated_job = {
        ...job,
        qt_completed: job.qt_planned,
        stage: 'completed',
        end: endDT.toISO(),
        active: false,
        current_batch: null,
        qt_released: job.qt_planned,
        progress: 100 
      }
      Vue.set(state, 'working_job_data', updated_job)
    }
  },

  actions: {
    loadJobData({ commit }, job_key) {
      return new Promise( resolve => {
        api.get(`job/${job_key}`)
        .then( resp => {
          commit('LOAD_WORKING_JOB_DATA', resp.data.detail) 
          resolve() 
        })
        .catch( err => window.alert(err) )
      })
    },

    startJob({ commit, state }) {
      const now = DT.utc()
      
      const new_work_session = createWorkSession(state, now)
      const new_batch = createBatch(state, now)

      // job update
      const job_update = {
        start: now.toISO(),
        stage: 'started',
        active: true,
      }

      const updated_job_data = {...state.working_job_data, ...job_update}

      /* INSERT EVENT CREATION HERE */
      const user_id = state.user._id
      const job = state.working_job_data
      const event = {
        event_type: 'JOB_STARTED',
        user_id,
        user_session_id: state.user_session._id,
        job_id: job._id,
        phase_id: job.phase_id,
        timestamp: now.toISO()
      }

      api.post('/event', event).then(() => {
        const payload = {
          new_work_session, 
          new_batch, 
          updated_job_data
        }
        commit('START_JOB', payload)
      })
    },

    pauseJob({ commit, state }) {
      return new Promise( resolve => {

        const now = DT.utc()
        const updated_work_session = getClosedWorkSessionData(state, now)

        /* INSERT EVENT CREATION HERE */
        const user_id = state.user._id
        const job = state.working_job_data

        const event = {
          event_type: 'JOB_PAUSED',
          user_id,
          user_session_id: state.user_session._id,
          job_id: job._id,
          phase_id: job.phase_id,
          timestamp: now.toISO()
        }

        api.post('/event', event).then(() => {
          commit('CLOSE_WORK_SESSION', updated_work_session)
          resolve()
        })
      })
    },

    resumeJob({ commit, state }) {
      return new Promise( resolve => {
        const now = DT.utc()
        const new_work_session = createWorkSession(state, now)
        
        /* INSERT EVENT CREATION HERE */
        const user_id = state.user._id
        const job = state.working_job_data

        const event = {
          event_type: 'JOB_RESUMED',
          user_id,
          user_session_id: state.user_session._id,
          job_id: job._id,
          phase_id: job.phase_id,
          timestamp: now.toISO()
        }

        api.post('/event', event).then( () => {
          commit('RESUME_JOB', new_work_session) 
          resolve()
        })
      })
    },

    completeStep({ commit }, step_index) {
      return new Promise( resolve => {
        const now = DT.utc()

        /* INSERT EVENT CREATION HERE */
        

        commit('COMPLETE_STEP', step_index)
        resolve()
      })
    },

    declareBatch({ commit, state }, batch_qt) {
      return new Promise( resolve => {
        const now = DT.utc()

        const job = state.working_job_data
        const remaining_qt = job.qt_planned - job.qt_completed
        const batch_is_last = batch_qt === remaining_qt
        

        /* INSERT EVENT CREATION HERE */ 

        
        if (batch_is_last) {
          const updated_work_session = getClosedWorkSessionData(state, now)
          commit('COMPLETE_JOB', now)
          commit('CLOSE_WORK_SESSION', updated_work_session)
        }
        else {
          const new_batch = createBatch(state, now)
          const new_completed_qt = job.qt_completed + batch_qt
          const payload = {
            qt_completed: new_completed_qt,
            new_batch
          }
          commit('COMPLETE_BATCH', payload)
        }
        resolve()
      })
    }
  }
}

export default traceability