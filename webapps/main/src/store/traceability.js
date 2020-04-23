import Vue from 'vue'
import { api } from '@/lib/apiCall.js'
import { DateTime as DT } from 'luxon'


/* ******* TEMPLATES *************

NEW WORK SESSION
{
  _id,
  start,
  user_id,
  user_session_id,
  job_id,
  status='active'
}

class WorkSession(FlexModel):
  id: str = Field(None, alias="_id")
  user_session: str
  job: str
  user: str
  # master_session: bool
  start: datetime = None
  end: datetime = None
  duration: timedelta = None


NEW ITERATION 
{
  _id,
  work_sessions: [current_work_session],
  job_id,
  start,
  shown_step_index = 0, // if procedure.length > 0
}

class Iteration(FlexModel):
  id: str = Field(..., alias="_id")
  job: str = None

  start: datetime
  end: datetime
  duration: timedelta = None

  qt_pass: float = None
  qt_scrap: float = None

  shown_step_index: int = None
  step_data: List[StepExecutionData]
  
  work_session_list: List[str] = []


*/

function createWorkSession(state, startDT) {
  const job_id = state.working_job_data._id
  const user_id = state.user._id
  const user_session_id = state.user_session._id
  
  // new work session
  const ws_key = state.user_session._key + startDT.ts
  const ws_start = startDT.toISO()
  
  return {
    _key: ws_key,
    start: ws_start,
    user_session_id,
    user_id,
    job_id,
    active: true
  }
}

function createIteration(state, startDT) {
  const job = state.working_job_data
  const job_id = job._id
  const iteration_key = job._key + startDT.ts
  const new_iteration = {
    _key: iteration_key,
    job_id,
    start: startDT.toISO(),
  }

  const procedure = state.working_job_data.step_sequence
  if (procedure.length) new_iteration.procedure = procedure.map( step => {
    return {
      _id: step._id,
      done: false,
      critical: false,
      user_data: []
    }
  })

  return new_iteration
}

// function addWorkSessionToIteration(state, ws_key) {
//   const current_iteration = state.iteration_list[state.iteration_list.length - 1]
  
//   current_iteration.work_session_list.push({
//     _key: ws_key,
//     full_session: null,
//     duration: null
//   })
// }



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
    // iteration_list: [],
    current_iteration_data: {},
  },

  getters: {
    getIterationStepUserData: state => step_id => {
      const iteration_procedure = state.current_iteration_data.procedure
      if (iteration_procedure) {
        const iteration_step = iteration_procedure.find( step => step._id === step_id )
        return iteration_step.user_data
      }
      else return []
    }
  },

  mutations: {

    START_USER_SESSION(state, session_data) {
      Vue.set(state, 'user', session_data)
    },

    LOAD_WORKING_JOB_DATA(state, job_data) {
      Vue.set(state, 'working_job_data', job_data)
    },

    START_JOB(state, {new_work_session, new_iteration, updated_job_data}) {
      // get timestamp and state metadata
      state.work_session_list.push(new_work_session)
      // state.iteration_list.push(new_iteration)
      Vue.set(state, 'current_iteration_data', new_iteration)
      // const current_iteration = state.iteration_list[state.iteration_list.length - 1]
      // current_iteration.work_session_list.push({
      //   _id: new_work_session._id,
      //   full_session: null,
      //   duration: null
      // })
      // addWorkSessionToIteration(new_work_session._key)
      Vue.set(state, 'working_job_data', updated_job_data)
    },

    CLOSE_WORK_SESSION(state, updated_work_session) {
      // Update general list of work sessions
      const ws_list_length = state.work_session_list.length
      Vue.set(state.work_session_list, ws_list_length-1, updated_work_session)

      // Update work sessions within the iteration
      // const current_iteration = state.iteration_list[state.iteration_list.length - 1]
      // const iteration_work_sessions = current_iteration.work_session_list
      // const last_iteration_work_session = iteration_work_sessions[iteration_work_sessions.length - 1]

      // const full_work_session_within_same_iteration = 
      //   updated_work_session.iteration_start === updated_work_session.iteration_end

      // const work_session_duration_within_iteration = 
      //   DT.fromISO(updated_work_session.end) - Math.max()

      // const iteration_session_update = {
      //   full_session: full_work_session_within_same_iteration,
      //   duration: 

      // Update Job status
      Vue.set(state.working_job_data, 'active', false)
    },

    RESUME_JOB(state, new_work_session) {
      state.work_session_list.push(new_work_session)      
      Vue.set(state.working_job_data, 'active', true)
      Vue.set(state.working_job_data, 'last_work_session_started', new_work_session._key)
    },

    COMPLETE_STEP(state, step_index) {
      Vue.set(state.current_iteration_data.procedure[step_index], 'done', true)
    },

    UPDATE_USER_DATA(state, { step_id, value_index, value }) {
      const iteration_data = state.current_iteration_data
      const step_data = iteration_data.procedure.find( step => step._id === step_id )
      Vue.set(step_data.user_data, value_index, value)
    },

    UPDATE_COMPLETED_QT(state, { qt_completed, new_iteration }) {
      Vue.set(state.working_job_data, 'qt_completed', qt_completed)
      Vue.set(state, 'current_iteration_data', new_iteration)
    },
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
      
      // const job_id = state.working_job_data._id
      // const user_id = state.user._id
      // const user_session_id = state.user_session._id
      
      // // new work session
      // const ws_key = state.user_session._key + now.ts
      // const ws_start = now.toISO()
      
      const new_work_session = createWorkSession(state, now)

      // new iteration
      // const iteration_key = state.working_job_data._key + now.ts
      // const new_iteration = {
      //   _key: iteration_key,
      //   job_id,
      //   start: now.toISO(),
      // }
      // const procedure = state.working_job_data.step_sequence
      // if (procedure.length) new_iteration.procedure = procedure.map( step => {
      //   return {
      //     _id: step._id,
      //     done: false,
      //     critical: false,
      //     user_data: []
      //   }
      // })
      const new_iteration = createIteration(state, now)

      // job update
      const job_update = {
        start: now.toISO(),
        stage: 'started',
        last_work_session_started: new_work_session._key,
        current_iteration: new_iteration._key,
        active: true,
      }

      const updated_job_data = {...state.working_job_data, ...job_update}

      /* INSERT EVENT CREATION HERE
       *
       *
       *
       *
       */

      const payload = {
        new_work_session, 
        new_iteration, 
        updated_job_data
      }
      commit('START_JOB', payload)
    },

    closeWorkSession({ commit, state }) {
      return new Promise( resolve => {
        const now = DT.utc()
        const ws_list_length = state.work_session_list.length
        const current_work_session = state.work_session_list[ws_list_length-1]
        // const ws_start = DT.fromISO(current_work_session.start)
        // const current_iteration_key = state.iteration_list.slice(-1)[0]._key

        const updated_work_session = {
          ...current_work_session,
          end: now.toISO(),
          // duration: now.diff(ws_start).milliseconds,
          // iteration_end: current_iteration_key
          active: false
        }

        /* INSERT EVENT CREATION HERE
         *
         *
         *
         *
         */

        commit('CLOSE_WORK_SESSION', updated_work_session)
        resolve()
      })
    },

    resumeJob({ commit, state }) {
      const now = DT.utc()
      const new_work_session = createWorkSession(state, now)
      
      /* INSERT EVENT CREATION HERE
       *
       *
       *
       *
       */  

      commit('RESUME_JOB', new_work_session)
    },

    completeStep({ commit }, step_index) {
      return new Promise( resolve => {
        // const now = DT.utc()

        /* INSERT EVENT CREATION HERE
         *
         *
         *
         *
         */  

        commit('COMPLETE_STEP', step_index)
        resolve()
      })
    },

    declareBatch({ commit, state }, batch_qt) {
      return new Promise( resolve => {
        const now = DT.utc()

        const job = state.working_job_data
        const remaining_qt = job.qt_planned - job.qt_completed
        const iteration_is_last = batch_qt === remaining_qt
        
        /* INSERT EVENT CREATION HERE
         *
         *
         *
         *
         */ 

        
        if (iteration_is_last) {
          commit('COMPLETE_JOB')
        }
        else {
          const new_iteration = createIteration(state, now)
          const new_completed_qt = job.qt_completed + batch_qt
          const payload = {
            qt_completed: new_completed_qt,
            new_iteration
          }
          commit('UPDATE_COMPLETED_QT', payload)
        }
        resolve()
      })
    }
  }
}

export default traceability