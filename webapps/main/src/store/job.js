import Vue from 'vue'
import { api } from '@/lib/apiCall.js'

const job = {

  state: {
    job_list: [],
    assigned_job_list: [],
    unassigned_job_list: [],
    temp_job_data: {},
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

    loadJobAssignments({ commit }) {
      api
        .get('job-assignment')
        .then(resp => {
          commit('LOAD_ASSIGNMENTS', resp.data.detail)
        })
    },

    updateJobs({ dispatch }, { job_updates, wo_key }) {
      return new Promise((resolve, reject) => {
        console.log(wo_key)
        api.post(`job/update`, job_updates)
        .then( () => {
          console.log(wo_key)
          dispatch('loadWorkOrderData', wo_key)
          .then( () => resolve() )
        })
        .catch( err => reject(err))
      })
    }
  }
}

export default job