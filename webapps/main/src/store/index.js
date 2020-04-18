import Vue from "vue";
import Vuex from "vuex";

import product from "@/store/product"
import process from "@/store/process"
import bom from "@/store/bom"
import user from "@/store/user"
import session from "@/store/session"
import workorder from "@/store/workorder"
import job from "@/store/job"
import org from "@/store/org"
import nav from "@/store/nav"
import traceability from "@/store/traceability"





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
