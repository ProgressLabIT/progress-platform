import Vue from "vue";
import Vuex from "vuex";
import { DateTime as DT } from 'luxon';

// import { persistSession } from "@/plugins/persistence"
import { resetSessionTimeoutAtStoreChange } from "@/plugins/session"

import product from "./product"
import process from "./process"
import bom from "./bom"
import user from "./user"
import workorder from "./workorder"
import job from "./job"
import org from "./org"
import nav from "./nav"
import traceability from "./traceability"
import session from "./session"

import { dark, light } from '@/styles/theme.js'



Vue.use(Vuex);
console.log(dark, light)

const store = new Vuex.Store({
  
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
      Vue.set(state, 'screen_title', new_title)
    },
    SET_THEME(state, theme) {
      Vue.set(state, 'theme_colors', theme)
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
    product,
    process,
    bom,
    user,
    workorder,
    job,
    org,
    nav,
    traceability,
    session
  }
});

export default store


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
