import Vue from 'vue'
import { cloneDeep as _cloneDeep } from 'lodash'
import { api } from '@/lib/apiCall.js'
import axios from 'axios'

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

    ADD_TEMP_MEDIA(state, { phase_no, step_no, media }) {
      let phase = state.temp[phase_no]
      let step = phase.steps[step_no]
      step.media.push(media)
    },

    DELETE_SAVED_MEDIA(state, { phase_no, step_no, index }) {
      let phase = state.temp[phase_no]
      let step = phase.steps[step_no]
      let media = step.media[index]
      Vue.set(media, 'trash', true)
    },

    RESTORE_SAVED_MEDIA(state, { phase_no, step_no, index }) {
      let phase = state.temp[phase_no]
      let step = phase.steps[step_no]
      let media = step.media[index]
      Vue.set(media, 'trash', false)
    },

    DELETE_TEMP_MEDIA(state, { phase_no, step_no, index }) {
      let phase = state.temp[phase_no]
      let media_list = phase.steps[step_no].media
      media_list.splice(index, 1)
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
      Vue.set(state, 'temp', _cloneDeep(state.saved))
    }
  },

  actions: {
    getOperations({commit}) {
      api.get('operation').then(resp => {
        commit('LOAD_OPERATIONS', resp.data)
      })
    },

    
    async getProcess({ commit }, product_key) {
      
      function get_step_media(step) {
        const step_key = step._id.split('/')[1]
        return new Promise( resolve => {
          api
          .get(`step/${step_key}/media`)
          .then( resp => {
            const media_list = resp.data.map( filename => {
              return {
                filename,
                src: `/media/step/${step_key}/${filename}`,
                temp: false,
                trash: false
              }
            })
            step.media = media_list
            resolve(step)
          })
        })
      }

      api
        .get(`product/${product_key}/process`)
        .then( async resp => {
          let phases = resp.data
          let promises = []
          for (let phase of phases) {
            for (let step of phase.steps) {
              if (step.type === 'instruction') {
                promises.push(get_step_media(step))
              }
            }
          }
          await Promise.all(promises)
          commit('LOAD_SAVED_PROCESS', phases) 
        })

    },

    saveTempProcess({ dispatch }, data) {

      // map added/deleted media
      let new_media = []
      let deleted_media = []

      data.new_process.forEach( phase => {
        phase.steps.forEach( step => {
          
          if (typeof step.media == 'undefined') return

          step.media.forEach( media => {
            if (media.trash) deleted_media.push({
              step_key: step._id.split('/')[1],
              filename: media.filename
            })

            if (media.temp) new_media.push({
              step_key: step._id.split('/')[1],
              media_file: media.data
            })
          })
        })
      })

      // set up api calls
      let api_calls = []

      deleted_media.forEach( ({ step_key, filename }) => {
        api_calls.push( 
          api.delete(`step/${step_key}/media/${filename}`)
        )
      })

      new_media.forEach( ({ step_key, media_file }) => {
        let body = new FormData()
        body.append('media_file', media_file)
        api_calls.push(
          api.post(
            `step/${step_key}/media`, 
            body, 
            { headers: { 'Content-type': 'multipart/form-data' } }
          )
        )
      })

      api_calls.push(
        api.put(`product/${data.product_key}/process`, data.new_process)
      )

      // update process data
      return new Promise( (resolve, reject) => {
        axios.all(api_calls)
        .then(() => {
          dispatch('getProcess', data.product_key)
        })
        .then(resolve())
        .catch(err => reject(err))
      })
    }
  },
}

export default process