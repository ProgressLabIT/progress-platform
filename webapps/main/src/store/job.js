import Vue from 'vue'
import { api } from '@/lib/apiCall.js'

const job = {

  state: {
    job_list: []
  },

  mutations: {
    LOAD_JOBS(state, job_list) {
      Vue.set(state, 'job_list', job_list)
    }
  },

  actions: {
    loadJobs({ commit }) {
      api
        .get('job')
        .then( resp => {
          commit('LOAD_JOBS', resp.data.detail)
        })
    }
  }
}

export default job