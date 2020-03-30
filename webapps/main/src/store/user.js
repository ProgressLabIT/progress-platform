import Vue from 'vue'
import { api } from '@/lib/apiCall.js'



const user = {

  state: {
    user_list: []
  },

  getters: {
    operator_list: (state) => () => {
      return state.user_list.filter( u => u.roles.operator )
    }
  },

  mutations: {
    LOAD_USERS(state, user_list) {
      Vue.set(state, 'user_list', user_list)
    }
  },

  actions: {
    loadUsers({ commit }) {
      api
        .get('user')
        .then( resp => {
          commit('LOAD_USERS', resp.data.detail)
        })
    }
  }


}

export default user