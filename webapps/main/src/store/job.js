import Vue from 'vue'
import { api } from '@/lib/apiCall.js'

const job = {

  state: {
    job_list: [],
    assigned_job_list: [],
    unassigned_job_list: [],
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
      return new Promise((resolve, reject) => {
        api.get('job')
          .then( resp => {
            commit('LOAD_JOBS', resp.data.detail)
            resolve()
          })
          .catch(err => reject(err))
        })
    },

    loadJobAssignments({ commit }, operator_key) {
      return new Promise((resolve) => {
        api
        .get('job-assignment', {
          params: { user_id: operator_key }
        })
        .then(resp => {
          commit('LOAD_ASSIGNMENTS', resp.data.detail)
          resolve()
        })
      })
    },

    updateJobs({ dispatch }, { job_updates, wo_key }) {
      return new Promise((resolve, reject) => {
        api.post(`job/update`, job_updates)
        .then( () => {
          dispatch('loadWorkOrderData', wo_key)
          .then( () => resolve() )
        })
        .catch( err => reject(err))
      })
    }
  }
}

export default job