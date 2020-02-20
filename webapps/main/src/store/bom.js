import Vue from 'vue'
import { api } from '@/lib/apiCall.js'
// import axios from 'axios'

const bom = {

  state: {
    items: []
  },

  mutations: {
    UPDATE_BOM(state, new_bom) {
      Vue.set(state, 'items', new_bom)
    }
  },

  actions: {
    updateBom(context, { product_key, new_bom }) {
      return new Promise( resolve => {
        api
          .put(`product/${product_key}/bom`, new_bom)
          .then(async () => {
            await this.dispatch('loadBom', product_key)
            resolve()
          })
      })
    },

    getBom({ commit }, product_key) {
      return new Promise(resolve => {
        api
          .get(`product/${product_key}/bom`)
          .then( resp => {
            commit('UPDATE_BOM', resp.data) 
            resolve()
          })
      }) 
    }
  },

  getters: {

  }
}

export default bom