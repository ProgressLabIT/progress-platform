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
    
    session_timeout: 15, // minutes
    session_timer: null,
    session_locked: false,
    
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
    },

    TOGGLE_SESSION_LOCK(state, locked) {
      Vue.set(state, 'session_locked', locked)

    },
  },

  actions: { 
    logout({ commit, dispatch, state, rootState }) {
      return new Promise( async (resolve) => {
        const is_working = rootState.traceability.work_session_list.some( ws => ws.active )
        if (is_working) {
          await dispatch('pauseJob')
        }
        api.delete(`session/${state.session_key}`)
        .then( async () => {
          commit('CLOSE_USER_SESSION')
          router.push({ name: 'login' })

          if (state.session_locked) {
            await dispatch('unlockSession')
          }
          
          resolve()
        })
      })
    },

    setSessionTimeout({ commit, state }) {
      clearTimeout(state.session_timer)
      // clearTimeout(state.logout_timer)

      // const forceLogout = async () => {
      //   await dispatch('logout')
      //   commit('TOGGLE_SESSION_LOCK', false)
      // }

      const lockSession = () => {
        commit('TOGGLE_SESSION_LOCK', true)
        // Vue.set(state, 'logout_timer', setTimeout(forceLogout, state.hard_timeout * 60 * 1000))
      }

      Vue.set(state, 'session_timer', setTimeout(lockSession, state.session_timeout * 60 * 1000))
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

    userHomepage: state => {
      const home = state.user.home_page_name
      return home ? home : 'userJobs'
    }
  }

}

export default session