import Vue from 'vue'
import { cloneDeep as _cloneDeep } from 'lodash'
import { api } from '@/lib/apiCall.js'

const process = {

  state: {
    saved: [],
    temp: [],
    operations: [],
  },

  mutations: {
    /**
     * Use this mutation to add, remove
     * change sequence of process phases
     */
    UPDATE_PROCESS(state, process) {
      Vue.set(state, 'temp', process)
    },

    LOAD_SAVED_PROCESS(state, process) {
      Vue.set(state, 'saved', _cloneDeep(process))
      Vue.set(state, 'temp', _cloneDeep(process))
    },

    UPDATE_PHASE_PARAMS(state, { phase_no, param, value }) {
      Vue.set(state.temp[phase_no].params, param, value)
    },

    UPDATE_PROCEDURE(state, { phase_no, procedure }) {
      Vue.set(state.temp[phase_no], 'steps', procedure)
    },

    UPDATE_STEP_DETAILS(state,  { phase_no, step_no, field, value })  {
      let phase = state.temp[phase_no]
      let step = phase.steps[step_no]
      Vue.set(step, field, value)
    },

    ADD_OR_UPDATE_STEP(state, { phase_no, step_no, step_data}) {
      let procedure = state.temp[phase_no].steps
      Vue.set(procedure, step_no, step_data)
    },

    DELETE_STEP(state, { phase_no, step_no }) {
      let procedure = state.temp[phase_no].steps
      procedure.splice(step_no, 1)
    },

    DELETE_PHASE(state, phase_no) {
      state.temp.splice(phase_no, 1)
    },

    LOAD_OPERATIONS(state, op_list) {
      Vue.set(state, 'operations', op_list)
    },

    CANCEL_PROCESS_CHANGES(state) {
      const deep_copy = _cloneDeep(state.saved)
      Vue.set(state, 'temp', deep_copy)
    }
  },

  actions: {
    getOperations({commit}) {
      api.get('operation').then(resp => {
        commit('LOAD_OPERATIONS', resp.data)
      })
    },

    getProcess({ commit }, product_key) {
      api
        .get(`product/${product_key}/process`)
        .then( resp => {
          commit('LOAD_SAVED_PROCESS', resp.data) 

        })
    },

    saveTempProcess({ commit }, data) {
      return api
        .put(`product/${data.product_key}/process`, data.new_process)
        .then( resp => {
          commit('LOAD_SAVED_PROCESS', resp.data)
        })
    }
  },

  // getters: {
  //   phaseParams4Humans(state) {
      
  //   }
  // }
}

export default process