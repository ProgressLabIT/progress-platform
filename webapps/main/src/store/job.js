import Vue from 'vue'
import { api } from '@/lib/apiCall.js'

const job = {

  state: {
    job_list: [],
    assigned_job_list: [],
    unassigned_job_list: []
  },

  mutations: {
    LOAD_JOBS(state, job_list) {
      Vue.set(state, 'job_list', job_list)
    },
    
    LOAD_ASSIGNMENTS(state, data) {
      Vue.set(state, 'assigned_job_list', data.assigned_jobs_by_operator)
      Vue.set(state, 'unassigned_job_list', data.unassigned_jobs)
    },

  },

  actions: {
    loadJobs({ commit }) {
      api
        .get('job')
        .then( resp => {
          commit('LOAD_JOBS', resp.data.detail)
        })
    },

    loadJobAssignments({ commit }) {
      api
        .get('job-assignment')
        .then(resp => {
          commit('LOAD_ASSIGNMENTS', resp.data.detail)
        })
    }
  }
}

export default job