import Vue from 'vue'
// import { api } from '@/lib/apiCall.js'


const session = {

  state: {
    user: {
      name: 'Cristian',
      surname: 'Colombara',
      _id: 'User/12005330'
    },
    session: null,
    permissions: null
  },

  mutations: {
    START_SESSION(state, session_data) {
      Vue.set(state, 'user', session_data)
    }
  }
}

export default session