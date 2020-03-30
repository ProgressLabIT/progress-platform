import Vue from 'vue'

const nav = {

  state: {
    job_dep_code: '',
  },

  mutations: {
    UPDATE_JOB_DEP_NAV_STATE(state, dep_code) {
      Vue.set(state, 'job_dep_code', dep_code)
    }
  }
}

export default nav