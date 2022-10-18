import { store } from 'quasar/wrappers'
import { createStore } from 'vuex'
import { DateTime as DT } from 'luxon'

import session from "./session"

import { dark, light } from '@/boot/theme.js'

// import example from './module-example'

/*
 * If not building with SSR mode, you can
 * directly export the Store instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Store instance.
 */

function resetSessionTimeoutAtStoreChange (store) {
  const mutations_to_ignore = [
    'TOGGLE_SESSION_LOCK',
    'CLOSE_SESSION'
  ]
  store.subscribe((mutation) => {
    if (!mutations_to_ignore.includes(mutation.type)) {
      store.dispatch('setSessionTimeout')
    }
  })
}

export default createStore({
  state() {
    return {
      drag_options: {
        animation: 200,
        ghostClass: "ghost"
      },
      screen_title: 'progress',
      theme_colors: dark
    }
  },

  mutations: {
    UPDATE_SCREEN_TITLE(state, new_title) {
      state.screen_title = new_title
    },
    SET_THEME(state, theme) {
      state.theme_colors = theme
    }
  },

  actions: {
    changeTheme({ commit }, dark_mode_on) {
      commit('SET_THEME', dark_mode_on ? dark : light)
    }
  },

  getters: {
    theme: state => state.theme_colors
  },

  plugins: [resetSessionTimeoutAtStoreChange],

  modules: {
    session
  },
  // enable strict mode (adds overhead!)
  // for dev mode and --debug builds only
  strict: process.env.DEBUGGING
})

const persistedState = window.localStorage.getItem('TEMP_SESSION')

if (persistedState) {
  const restored_state = JSON.parse(persistedState)
  const elapsed_milliseconds = DT.utc().toMillis() - restored_state.last_interaction
  const FIVE_MINUTES_MILLISECONDS = 5 * 60 * 1000
  if (elapsed_milliseconds < FIVE_MINUTES_MILLISECONDS) {
    store.replaceState(restored_state)
    store.commit('TOGGLE_SESSION_LOCK', true)
  }
  window.localStorage.removeItem('TEMP_SESSION')
}
