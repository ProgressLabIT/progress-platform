import { DateTime as DT } from 'luxon'
import { debounce } from 'quasar'
import { createStore } from 'vuex'

import { dark, light } from '@/boot/theme.js'

import job from "./job"
import org from "./org"
import process from "./process"
import product from "./product"
import session from "./session"
import traceability from "./traceability"
import user from "./user"
import workorder from "./workorder"
import bom from "./bom"

// import example from './module-example'

/*
 * If not building with SSR mode, you can
 * directly export the Store instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Store instance.
 */

function resetSessionTimeoutAtStoreChange(store) {
  const mutations_to_ignore = [
    'TOGGLE_SESSION_LOCK',
    'CLOSE_SESSION',
    'SET_SESSION_TIMEOUT',
  ]
  store.subscribe( debounce((mutation) => {
    if (!mutations_to_ignore.includes(mutation.type)) {
      store.commit('SET_SESSION_TIMEOUT')
    }
  }, 5000))
}


const store = createStore({
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
    theme (state) {
      return state.theme_colors
    },
  },

  plugins: [resetSessionTimeoutAtStoreChange],

  modules: {
    bom,
    job,
    org,
    process,
    product,
    session,
    traceability,
    user,
    workorder
  }
})


/**
 * The following code restores the vuex state saved in localStorage
 * when closing or refreshing the tab, but locks the session, so the
 * user will have to input the password to proceed.
 *
 * If more than five minutes have elapsed since the close, the session
 * will not be restored.
 */
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

export default store
