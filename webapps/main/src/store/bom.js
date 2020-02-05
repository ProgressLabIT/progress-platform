import Vue from 'vue'
import { api } from '@/lib/apiCall.js'

const bom = {

  state: {
    items: []
  },

  mutations: {
    UPDATE_BOM(state, new_bom) {
      Vue.set(state.items, new_bom)
    }
  },

  actions: {
    
  },

  getters: {

  }
}

export default bom