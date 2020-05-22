import Vue from "vue";
import Vuex from "vuex";

import product from "./product"
import process from "./process"
import bom from "./bom"
import user from "./user"
// import session from "./session"
import workorder from "./workorder"
import job from "./job"
import org from "./org"
import nav from "./nav"
import traceability from "./traceability"





Vue.use(Vuex);

// import { updateListItemByKey as updateProduct } from '@/lib/ListUpdate.js'
// import axios from 'axios'
// import { api } from '@/lib/apiCall.js'


export default new Vuex.Store({
  
  state() {
    return {
      drag_options: {
        animation: 200,
        ghostClass: "ghost"
      },
      screen_title: ''
    }
  },

  getters: {},

  mutations: {
    UPDATE_SCREEN_TITLE(state, new_title) {
      Vue.set(state, 'screen_title', new_title)
    }
  },

  actions: {},

  modules: {
    product,
    process,
    bom,
    user,
    workorder,
    job,
    org,
    nav,
    traceability
  }
});
