import Vue from 'vue'
import { api } from '@/lib/apiCall.js'

const org = {

  state: {
    departments: [],
  },

  mutations: {
    LOAD_DEPARTMENTS(state, dep_list) {
      Vue.set(state, 'departments', dep_list)
    },
  },

  actions: {
    loadDepartments({ commit }) {
      return new Promise(resolve => {
        api
          .get('department')
          .then( resp => {
            commit('LOAD_DEPARTMENTS', resp.data.detail)
            resolve()
          })
      })
    },

  }
}

export default org