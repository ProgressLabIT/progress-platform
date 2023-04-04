import { api } from '@/boot/axios.js'
import { DateTime as DT } from 'luxon'

function createEmptyBatch(state, startDT, job) {
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

function createEvent(state, session_state, { event_type, timestamp, step_key=null, user_data=null, completed_batch_qt=null }) {
  const user_key = session_state.user._key
  const job = state.working_job_data

  const event = {
    event_type,
    user_key,
    user_session_key: session_state.session_key,
    job_key: job._key,
    product_key: job.product_key,
    work_order_key: job.wo_key,
    phase_key: job.phase_key,
    active_batch_key: job.active_batch_key,
    project_code: job.project_code,
    step_key,
    user_data,
    completed_batch_qt,
    timestamp // ISO format
  }

  return event
}

function getCurrentWorkSession(state) {
  const ws_count = state.work_session_list.length
  return state.work_session_list[ws_count-1]
}

function getClosedWorkSessionData(state, endDT) {
  const current_work_session = getCurrentWorkSession(state)

  const work_session = {
    ...current_work_session,
    end: endDT.toISO(),
    active: false
  }
  return work_session
}

function sendHeartBeat(state) {
  const job_key = state.working_job_data._key
  api.post(`/job/${job_key}/heartbeat`)
}


const traceability = {

  state: {
    working_job_data: {},
    work_session_list: [],
    current_batch_data: {},
    heartbeat: null
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
      state.user = user_data

      const session_data = { _key: data.session_key, scope: data.scope }
      state.user_session = session_data
    },

    LOAD_WORKING_JOB_DATA(state, {job_data, batch_data}) {
      state.working_job_data = job_data
      state.current_batch_data = batch_data
    },

    START_JOB(state, { batch_data, job_data}) {
      // get timestamp and state metadata
      state.current_batch_data = batch_data
      state.working_job_data = job_data
    },

    CLOSE_WORK_SESSION(state, work_session) {
      // Update general list of work sessions
      const ws_list_length = state.work_session_list.length
      state.work_session_list[ws_list_length-1] = work_session

      // Update Job status
      state.working_job_data.active = false
    },

    SET_HEARTBEAT(state, alive) {
      alive
        ? state.heartbeat = setInterval(() => sendHeartBeat(state), 10000)
        : clearInterval(state.heartbeat)
    },

    UPDATE_STEP_USER_DATA(state, { step_key, value_index, value }) {
      const step_data = this.getters.getBatchStep(step_key)
      step_data.user_data[value_index] = value
    },

    UPDATE_JOB(state, job_data) {
      state.working_job_data = {
        /* Use spread to avoid overwriting notes,
        which are not present in the event response */
        ...state.working_job_data,
        ...job_data
      }
    },

    UPDATE_BATCH(state, batch_data) {
      state.current_batch_data = batch_data
    }
  },

  actions: {
    loadWorkingJobData({ commit }, job_key) {
      return new Promise( async resolve => {
        // Get job data
        const job_resp = await api.get(`job/${job_key}`)
        const job_data = job_resp.data.detail

        // Get active batch data (if any)
        let batch_data = {}
        if (job_data.active_batch_key) {
          const batch_resp = await api.get(`batch/${job_data.active_batch_key}`)
          batch_data = batch_resp.data.detail
        }
        commit('LOAD_WORKING_JOB_DATA', {job_data, batch_data})
        resolve()
      })
    },

    startJob({ commit, state, rootState }) {
      const now = DT.utc()

      // Create Event
      const event = createEvent(state, rootState.session, {
        event_type: 'JOB_STARTED',
        timestamp: now.toISO()
      })

      // Post event and save new data
      api.post('event', event).then((resp) => {
        const { new_work_session_data, batch_data, job_data } = resp.data.detail
        commit('START_JOB', { new_work_session_data, batch_data, job_data })
        commit('SET_HEARTBEAT', true)
      })
    },

    pauseJob({ commit, state, rootState }) {
      return new Promise( (resolve, reject) => {
        const now = DT.utc()
        const work_session = getClosedWorkSessionData(state, now)

        const event = createEvent(state, rootState.session, {
          event_type: 'JOB_PAUSED',
          timestamp: now.toISO()
        })

        api.post('event', event).then(() => {
          commit('CLOSE_WORK_SESSION', work_session)
          commit('SET_HEARTBEAT', false)
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
        // const new_work_session = createWorkSession(state, rootState.session, now)

        const event = createEvent(state, rootState.session, {
          event_type: 'JOB_RESUMED',
          timestamp: now.toISO()
        })

        api.post('event', event).then( resp => {
          const { new_work_session_data, job_data, batch_data } = resp.data.detail
          commit('UPDATE_JOB', job_data)
          commit('UPDATE_BATCH', batch_data)
          commit('SET_HEARTBEAT', true)
          resolve()
        })
      })
    },

    completeStep({ commit, state, rootState }, { step_index, batch_qt }) {
      return new Promise( resolve => {
        const now = DT.utc()
        const step_data = state.current_batch_data.step_data[step_index] || null

        const event = createEvent(state, rootState.session, {
          event_type: 'STEP_COMPLETED',
          step_key: step_data._key,
          timestamp: now.toISO(),
          user_data: step_data.user_data,
          completed_batch_qt: batch_qt
        })

        api.post('event', event).then( resp => {
          const { job_data, batch_data } = resp.data.detail
          commit('UPDATE_JOB', job_data)
          commit('UPDATE_BATCH', batch_data)
          if (job_data.status === 'closed') {
            commit('SET_HEARTBEAT', false)
          }
          resolve()
        })
      })
    },

    declareBatch({ commit, state, rootState }, { batch_qt }) {
      return new Promise( resolve => {
        const now = DT.utc()
        /* INSERT EVENT CREATION HERE */
        const event = createEvent(state, rootState.session, {
          event_type: 'BATCH_COMPLETED',
          timestamp: now.toISO(),
          completed_batch_qt: batch_qt
        })

        api.post('event', event).then( resp => {
          let { job_data, batch_data } = resp.data.detail

          if ( !batch_data || !('step_data' in batch_data) ) {
            batch_data = createEmptyBatch(state, now, job_data)
          }

          commit('UPDATE_JOB', job_data)
          commit('UPDATE_BATCH', batch_data)

          if (job_data.status === 'closed') {
            commit('SET_HEARTBEAT', false)
          }
          resolve()
        })
      })
    },
  }
}

export default traceability
