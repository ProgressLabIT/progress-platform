import Vue from 'vue'
import { api } from '@/lib/apiCall.js'
import axios from 'axios'


const workorder = {

  state: {
    wo_list: [],
  },

  mutations: {
    LOAD_WORK_ORDERS(state, list) {
      Vue.set(state, 'wo_list', list)
    },
  },

  actions: {
    loadWorkOrders({ commit }) {
      api
        .get('work-order')
        .then( resp => {
          commit('LOAD_WORK_ORDERS', resp.data.detail)
        })
    },

    postWorkOrder({ dispatch }, wo_list) {
      return new Promise( (resolve, reject) => {
        let api_calls = wo_list.map( wo => {
          return api.post('work-order', wo)
        })
        axios.all(api_calls)
        .then(() => {
          dispatch('loadWorkOrders')
          .then(resolve())
        })
        .catch( err => reject(err))
      })
    }
  }

}

export default workorder