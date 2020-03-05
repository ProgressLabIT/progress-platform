import Vue from "vue";
import Vuex from "vuex";

import product from "@/store/product"
import process from "@/store/process"
import bom from "@/store/bom"
import user from "@/store/user"




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
    }
  },

  getters: {},

  mutations: {},

  actions: {},

  modules: {
    product,
    process,
    bom,
    user
  }
});
