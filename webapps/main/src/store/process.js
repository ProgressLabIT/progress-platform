import Vue from 'vue'

const process = {

  state: {
    phases: []
  },

  mutations: {
    /**
     * Use this mutation to add, remove
     * change sequence of process phases
     */
    UPDATE_PROCESS(state, process) {
      Vue.set(state, 'phases', process)
    },

    UPDATE_PROCEDURE(state, { phase_no, procedure }) {
      Vue.set(state.phases[phase_no], 'steps', procedure)
    },

    UPDATE_STEP_DETAILS(state,  { phase_no, step_no, field, value })  {
      let phase = state.phases[phase_no]
      let step = phase.steps[step_no]
      Vue.set(step, field, value)
    },

    ADD_OR_UPDATE_STEP(state, { phase_no, step_no, step_data}) {
      let procedure = state.phases[phase_no].steps
      Vue.set(procedure, step_no, step_data)
    },

    DELETE_STEP(state, { phase_no, step_no }) {
      let procedure = state.phases[phase_no].steps
      procedure.splice(step_no, 1)
    },

    DELETE_PHASE(state, phase_no) {
      state.phases.splice(phase_no, 1)
    }

  },

  actions: {

  },

  getters: {

  }
}

export default process