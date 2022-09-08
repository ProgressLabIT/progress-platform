import Vue from 'vue'
import router from '@/router/index'
import { api } from '@/lib/apiCall.js'

const session = {

  state: {
    user: {
      name: '',
      surname: '',
      _key: '',
      home_page_name: ''
    },
    session_key: '',
    auth_token: '',
    scope: '',
    
    max_idle_minutes: 15, // minutes
    session_locked: false,
    session_timer: undefined
    
    // hard_timeout: 2,
    // logout_timer: null,
  },


  mutations: {

    UPDATE_AUTH_TOKEN(state, new_token) {
      Vue.set(state, 'auth_token', new_token)
    },

    START_USER_SESSION(state, data) {
      const user_data = { name: data.name, surname: data.surname, _key: data.user_key }
      Vue.set(state, 'user', user_data)
      Vue.set(state, 'session_key', data.session_key)
      Vue.set(state, 'scope', data.scope)
      // Vue.set(state, 'session_timeout', data.timeout)
    },

    CLOSE_USER_SESSION(state) {
      Vue.set(state, 'user', { name: null, surname: null, _key: null })
      Vue.set(state, 'session_key', null)
      Vue.set(state, 'scope', null)
      Vue.set(state, 'auth_token', null)
      
      // Make sure to cancel any residual locking mechanism after logout
      clearTimeout(state.session_timer)
      Vue.set(state, 'session_locked', false)
    },

    TOGGLE_SESSION_LOCK(state, locked) {
      Vue.set(state, 'session_locked', locked)
    },
  },

  actions: { 
    logout({ commit, dispatch, state, rootState }) {
      return new Promise( async (resolve) => {
        const is_working = rootState.traceability.working_job_data.active || false
        if (is_working) {
          try {
            await dispatch('pauseJob')
          }
          catch {
            /* 
            Some edge cases caused by unknown bugs may leave active work sessions
            in the vuex store, triggering the puaseJob action, which will cause error
            because there are no active work sessions in the backend
            */
          }
        }
        api.delete(`session/${state.session_key}`)
        .then( async () => {
          commit('CLOSE_USER_SESSION')
          router.push({ name: 'login' })          
          resolve()
        })
      })
    },

    setSessionTimeout({ commit, state }) {
      clearTimeout(state.session_timer)

      const lockSession = () => {
        commit('TOGGLE_SESSION_LOCK', true)
      }
    
      Vue.set(state, 'session_timer', setTimeout(lockSession, state.max_idle_minutes * 60 * 1000))
    },

    unlockSession({ commit, dispatch }) {
      commit('TOGGLE_SESSION_LOCK', false)
      dispatch('setSessionTimeout')
    },
  },

  getters: {
    getToken: state => {
      return state.auth_token
    },

    isLoggedIn: state => {
      let token = state.auth_token
      let session = state.session_key
      let user = state.user._key

      return  token && user && session
    },

    hasPermission: state => route_scope => {
      return RegExp(route_scope).test(state.scope)
    },

    userFullName: state => {
      return state.user.name + ' ' + state.user.surname
    },

    userHomepage: state => {
      let first_page = state.user.home_page_name

      const hasAdminScope = RegExp('admin').test(state.scope)
      const hasProductionScope = RegExp('production').test(state.scope)
      const hasLibrayScope = RegExp('library').test(state.scope)
      const hasOperatorScope = RegExp('operator').test(state.scope)

      if (hasOperatorScope) { first_page = 'operatorRoot' }
      else if (hasProductionScope) { first_page = 'productionRoot'}
      else if (hasLibrayScope) { first_page = 'libraryRoot' }
      else if (hasAdminScope) { first_page = 'adminPanel' }

      return first_page
    }
  }

}

export default session
