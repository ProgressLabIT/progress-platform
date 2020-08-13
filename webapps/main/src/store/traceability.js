import Vue from 'vue'
import { api } from '@/lib/apiCall.js'
import { DateTime as DT } from 'luxon'

function createWorkSession(state, session_state, startDT) {
  const job_key = state.working_job_data._key
  const user_key = session_state.user._key
  const user_session_key = session_state.user_session_key
  
  const ws_start = startDT.toISO()
  
  return {
    start: ws_start,
    user_session_key,
    user_key,
    job_key,
    active: true
  }
}

function createBatch(state, startDT) {
  const job = state.working_job_data
  const job_key = job._key
  const new_batch = {
    job_key,
    start: startDT.toISO(),
  }

  const procedure = state.working_job_data.step_sequence
  if (procedure.length) new_batch.step_data = procedure.map( step => {
    return {
      _key: step._key,
      type: step.type,
      done: false,
      critical: false,
      user_data: []
    }
  })

  return new_batch
}

function createEvent(state, session_state, { event_type, timestamp, step_key, user_data, completed_batch_qt }) {
  const user_key = session_state.user._key
  const job = state.working_job_data

  const event = {
    event_type,
    user_key,
    user_session_key: session_state.session_key,
    job_key: job._key,
    phase_key: job.phase_key,
    step_key,
    user_data,
    completed_batch_qt,
    timestamp // ISO format
  }

  return event
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
    working_job_data: {},
    work_session_list: [],
    current_batch_data: {},
  },

  getters: {
    getBatchStep: state => step_key => {
      const batch_procedure = state.current_batch_data.step_data
      if (batch_procedure) {
        const batch_step = batch_procedure.find( step => step._key === step_key )
        return batch_step
      }
      else return []
    }
  },

  mutations: {

    START_USER_SESSION(state, data) {
      const user_data = { name: data.name, surname: data.surname, _key: data.user_key }
      Vue.set(state, 'user', user_data)
      
      const session_data = { _key: data.session_key, scope: data.scope }
      Vue.set(state, 'user_session', session_data)
    },

    LOAD_WORKING_JOB_DATA(state, {job_data, batch_data}) {
      Vue.set(state, 'working_job_data', job_data)
      Vue.set(state, 'current_batch_data', batch_data)
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
      Vue.set(state.current_batch_data.step_data[step_index], 'done', true)
    },

    UPDATE_STEP_USER_DATA(state, { step_key, value_index, value }) {
      const step_data = this.getters.getBatchStep(step_key)
      Vue.set(step_data.user_data, value_index, value)
    },

    COMPLETE_BATCH(state, { qt_completed, new_batch }) {
      Vue.set(state.working_job_data, 'qt_completed', qt_completed)
      Vue.set(state, 'current_batch_data', new_batch)
    },

    CLOSE_JOB(state, endDT) {
      const job = state.working_job_data
      const updated_job = {
        ...job,
        stage: 'closed',
        end: endDT.toISO(),
        active: false,
        current_batch: null,
        // qt_released: job.qt_planned,
        progress: 100 
      }
      Vue.set(state, 'working_job_data', updated_job)
    }
  },

  actions: {
    loadJobData({ commit }, job_key) {
      return new Promise( async resolve => {
        // Get job data
        const job_resp = await api.get(`job/${job_key}`)
        const job_data = job_resp.data.detail

        // Get active batch data (if any)
        let batch_data = {}
        const active_batch_key = job_data.current_batch
        if (active_batch_key) {
          const batch_key = active_batch_key.split('/')[1]
          const batch_resp = await api.get(`batch/${batch_key}`)
          batch_data = batch_resp.data.detail
        }     
        commit('LOAD_WORKING_JOB_DATA', {job_data, batch_data}) 
        resolve() 
      })
    },

    startJob({ commit, state, rootState }) {
      const now = DT.utc()
      
      const new_work_session = createWorkSession(state, rootState.session, now)
      const new_batch = createBatch(state, now)

      // job update
      const job_update = {
        start: now.toISO(),
        stage: 'started',
        active: true,
      }

      const updated_job_data = {...state.working_job_data, ...job_update}

      /* INSERT EVENT CREATION HERE */
      const user_key = rootState.session.user._key
      const job = state.working_job_data
      const event = {
        event_type: 'JOB_STARTED',
        user_key,
        user_session_key: rootState.session.session_key,
        job_key: job._key,
        phase_key: job.phase_key,
        timestamp: now.toISO()
      }

      api.post('event', event).then(() => {
        const payload = {
          new_work_session, 
          new_batch, 
          updated_job_data
        }
        commit('START_JOB', payload)
      })
    },

    pauseJob({ commit, state, rootState }) {
      return new Promise( (resolve, reject) => {
        const now = DT.utc()
        const updated_work_session = getClosedWorkSessionData(state, now)

        /* INSERT EVENT CREATION HERE */
        const user_key = rootState.session.user._key
        const job = state.working_job_data

        const event = {
          event_type: 'JOB_PAUSED',
          user_key,
          user_session_key: rootState.session.session_key,
          job_key: job._key,
          phase_key: job.phase_key,
          timestamp: now.toISO()
        }

        api.post('event', event).then(() => {
          commit('CLOSE_WORK_SESSION', updated_work_session)
          resolve()
        })
        .catch(() => {
          reject()
        })
      })
    },

    resumeJob({ commit, state, rootState }) {
      return new Promise( resolve => {
        const now = DT.utc()
        const new_work_session = createWorkSession(state, rootState.session, now)
        
        /* INSERT EVENT CREATION HERE */
        const user_key = rootState.session.user._key
        const job = state.working_job_data

        const event = {
          event_type: 'JOB_RESUMED',
          user_key,
          user_session_key: rootState.session.session_key,
          job_key: job._key,
          phase_key: job.phase_key,
          timestamp: now.toISO()
        }

        api.post('event', event).then( () => {
          commit('RESUME_JOB', new_work_session) 
          resolve()
        })
      })
    },

    completeStep({ commit, state, rootState }, { step_index, last_step, last_batch, batch_qt }) {
      return new Promise( resolve => {
        const now = DT.utc()

        const job = state.working_job_data
        const step_data = state.current_batch_data.step_data[step_index]

        const commitChanges = () => {
          commit('COMPLETE_STEP', step_index)
          if (last_step) {
           
            const new_batch = last_batch ? {} : createBatch(state, now)
            const new_completed_qt = job.qt_completed + batch_qt
            commit('COMPLETE_BATCH', { qt_completed: new_completed_qt, new_batch })
           
            if (last_batch) {
              commit('CLOSE_JOB', now)
            }
          }
        }

        const event = createEvent(state, rootState.session, {
          event_type: 'STEP_COMPLETED',
          step_key: step_data._key,
          timestamp: now.toISO(),
          user_data: step_data.user_data,
          completed_batch_qt: batch_qt
        })
        api.post('event', event).then(() => {
          commitChanges()
          resolve()
        })
      })
    },

    declareBatch({ commit, state, rootState }, { batch_qt, last_batch }) {
      return new Promise( resolve => {
        const now = DT.utc()
        const job = state.working_job_data
        const commitChanges = () => {
          const new_completed_qt = job.qt_completed + batch_qt
          const new_batch = last_batch ? {} : createBatch(state, now)
          commit('COMPLETE_BATCH', { qt_completed: new_completed_qt, new_batch })

          if (last_batch) {
            commit('CLOSE_JOB', now)
          }
        }


        /* INSERT EVENT CREATION HERE */ 
        const event = createEvent(state, rootState.session, {
          event_type: 'BATCH_COMPLETED',
          timestamp: now.toISO(),
          completed_batch_qt: batch_qt
        })

        api.post('event', event).then(() => {
          commitChanges()
          resolve()
        })
      })
    },
  }
}

export default traceability