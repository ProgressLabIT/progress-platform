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
    iteration_list: [],
    iteration_user_data: [],
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
      state.iteration_list.push(new_iteration)
      Vue.set(state, 'working_job_data', updated_job_data)
    },
  },

  actions: {
    loadJobData({ commit }, {job_key}) {
      api.get(`job/${job_key}`)
      .then( resp => commit('LOAD_WORKING_JOB_DATA', resp.data.detail) )
      .catch( err => window.alert(err) )
    },

    startJob({ commit, state }) {
      const now = DT.utc()
      
      const job_id = state.working_job_data._id
      const user_id = state.user._id
      const user_session_id = state.user_session._id
      
      // new work session
      const ws_key = state.user_session._key + now.ts
      const ws_start = now.toISO()
      
      const new_work_session = {
        _key: ws_key,
        start: ws_start,
        user_session_id,
        user_id,
        job_id,
        active: true
      }

      // new iteration
      const iteration_key = state.working_job_data._key + now.ts
      const iteration_id = 'Iteration/' + iteration_key
      const ws_id = 'WorkSession/' + ws_key

      const current_work_session = {
        _id: ws_id,
        full_session: true,
        duration: null
      }
      
      const new_iteration = {
        _key: iteration_key,
        job_id,
        start: now.toISO(),
        work_session_list: [current_work_session],
      }

      const procedure = state.working_job_data.step_sequence
      const step_check = state.working_job_data.parameters.step_check
      if (procedure.length && step_check) new_iteration.next_step = 0


      // job update
      const job_update = {
        start: now.toISO(),
        stage: 'started',
        last_work_session_started: ws_id,
        active: true,
        current_iteration: iteration_id,
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
    }
  }
}

export default traceability