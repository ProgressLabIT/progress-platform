import Vue from "vue";
import Vuex from "vuex";

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





Vue.use(Vuex);

const store = new Vuex.Store({
  
  state() {
    return {
      drag_options: {
        animation: 200,
        ghostClass: "ghost"
      },
      screen_title: '',
    }
  },

  mutations: {
    UPDATE_SCREEN_TITLE(state, new_title) {
      Vue.set(state, 'screen_title', new_title)
    },
  },

  actions: {},
  getters: {},

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

const persistedState = window.localStorage.getItem('TEMP_SESSION')

if (persistedState) {
  store.replaceState(JSON.parse(persistedState))
  store.commit('TOGGLE_SESSION_LOCK', true)
  window.localStorage.removeItem('TEMP_SESSION')
}
