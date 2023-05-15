import { api, axios } from '@/boot/axios.js'

const workorder = {

  state: {
    wo_map: {},
    temp_queue: [],
    saved_queue: [],
    wo_data: {},
  },

  mutations: {
    LOAD_WORK_ORDERS(state, list) {
      state.saved_queue = []
      state.temp_queue = []
      list.forEach( (wo, index) => {
        state.wo_map[wo._key] = {...wo, sequence: index + 1}
        state.saved_queue.push(wo._key)
        state.temp_queue.push(wo._key)
      })
    },

    LOAD_WORK_ORDER_DATA(state, wo_data) {
      state.wo_data = wo_data
    },

    UPDATE_WO_LIST(state, wo_updates) {
      wo_updates.forEach( (wo, index) => state.wo_map[wo._key] = {
        ...wo,
        sequence: index + 1
      })
    },

    UPDATE_TEMP_QUEUE(state, { new_queue_index, old_queue_index }) {
      const selected_wo = state.temp_queue.splice(old_queue_index, 1)[0]
      state.temp_queue.splice(new_queue_index, 0, selected_wo)
    },

    RESET_TEMP_QUEUE(state) {
      state.temp_queue = [...state.saved_queue]
    }
  },

  actions: {
    loadWorkOrders({ commit }) {
      return new Promise( resolve => {
        api
          .get(`queue/site/0`)
          .then( resp => {
            commit('LOAD_WORK_ORDERS', resp.data.detail)
            resolve()
          })
      })
    },

    // Differs from the above because it doesn't change the queue
    updateWorkOrderList({ commit }) {
      return new Promise( resolve => {
        api
          .get(`queue/site/0`)
          .then( resp => {
            commit('UPDATE_WO_LIST', resp.data.detail)
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

    updateWorkOrder({ dispatch }, { wo_key, new_qt, new_due_date, new_from_date, new_project_code, job_updates, notes }) {
      return new Promise( (resolve, reject) => {
        const updates = []
        updates.push( api.patch(`work-order/${wo_key}`, { new_qt, new_due_date, new_from_date, new_project_code, notes }) )
        
        if (job_updates) {
          updates.push(api.post(`job/update`, job_updates))
        }

        axios.all(updates)
        .then(resolve)
        .catch( err => reject(err) )
      })
    },

    saveQueueChanges({ dispatch, state }) {
      return new Promise( (resolve) => {
        const queue_update = {
          type: 's',
          // Use default site until full multi-site management is implemented
          site_key: '0',
          work_orders: state.temp_queue
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
