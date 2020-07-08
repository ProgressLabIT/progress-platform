import Vue from 'vue'
import { api } from '@/lib/apiCall.js'
import { cloneDeep as _cloneDeep } from 'lodash'
import axios from 'axios'


const workorder = {

  state: {
    wo_list: [],
    temp_wo_list: [],
    wo_data: {},
  },

  mutations: {
    LOAD_WORK_ORDERS(state, list) {
      Vue.set(state, 'wo_list', list)
    },

    LOAD_WORK_ORDER_DATA(state, wo_data) {
      Vue.set(state, 'wo_data', wo_data)
    },

    SET_TEMP_QUEUE(state) {
      const list_with_sequence_index = state.wo_list.map( (wo, index) => {
        return { ..._cloneDeep(wo), sequence: index + 1 }
      })

      Vue.set(state, 'temp_wo_list', list_with_sequence_index)
    },

    UPDATE_TEMP_QUEUE(state, { newIndex, oldIndex }) {
      const selected_wo = state.temp_wo_list.splice(oldIndex, 1)[0]
      state.temp_wo_list.splice(newIndex, 0, selected_wo)
    },
  },

  actions: {
    loadWorkOrders({ commit }) {
      return new Promise( resolve => {
        api
          .get(`queue/site/0`)
          .then( resp => {
            commit('LOAD_WORK_ORDERS', resp.data.detail)
            commit('SET_TEMP_QUEUE')
            resolve()
          })
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
    },

    loadWorkOrderData({ commit }, wo_key) {
      return new Promise( (resolve, reject) => {
        api
        .get(`work-order/${wo_key}`)
        .then( resp => {
          commit('LOAD_WORK_ORDER_DATA', resp.data.detail)
          resolve()
        })
        .catch( err => reject(err) )
      })
    },

    updateWorkOrder({ dispatch }, { wo_key, new_qt, new_due_date, job_updates }) {
      return new Promise( (resolve, reject) => {
        const updates = []
        updates.push( api.patch(`work-order/${wo_key}`, { new_qt, new_due_date }) )
        
        if (new_qt && job_updates) {
          updates.push(api.post(`job/update`, job_updates))
        }

        axios.all(updates)
        .then( () => {
          dispatch('loadWorkOrderData', wo_key)
          .then(() => resolve())
        })
        .catch( err => reject(err) )
      })
    },

    saveQueueChanges({ dispatch, state }) {
      return new Promise( (resolve) => {
        const queue_update = {
          type: 's',
          // Use default site until full multi-site management is implemented
          site_key: '0',
          work_orders: state.temp_wo_list.map( wo => wo._key )
        }
        api
        .put('queue', queue_update)
        .then( async () => {
          await axios.all([
            dispatch('loadWorkOrders'),
            dispatch('loadJobAssignments')
          ])
          resolve()
        })
      })
    }
  }

}

export default workorder