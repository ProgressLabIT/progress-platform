import Vue from 'vue'
import { api } from '@/lib/apiCall.js'

const worksession = {

  state: {
    session_job_data: {},
    run_data: [],
  },

  mutations: {

    LOAD_SESSION_JOB_DATA(state, job_data) {
      Vue.set(state, 'session_job_data', job_data)
    }
  },

  actions: {
    loadJobData({ commit }, {job_key, phase_key}) {
      api.get(`job/${job_key}`)
      .then( resp => commit('LOAD_SESSION_JOB_DATA', resp.data.detail) )
      .catch( err => window.alert(err) )
    },


  }
}

export default worksession