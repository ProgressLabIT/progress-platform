import { cloneDeep as _cloneDeep } from 'lodash'
import { api, axios } from '@/boot/axios.js'

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
      state.temp = process
    },

    LOAD_SAVED_PROCESS(state, process) {
      state.saved = _cloneDeep(process)
      state.temp = _cloneDeep(process)
    },

    UPDATE_PHASE_PARAMS(state, { phase_index, param, value }) {
      state.temp[phase_index].params[param] = value
    },

    UPDATE_PROCEDURE(state, { phase_index, procedure }) {
      state.temp[phase_index].steps = procedure
    },

    UPDATE_STEP_DETAILS(state,  { phase_index, step_index, field, value })  {
      state.temp[phase_index].steps[step_index][field] = value
    },

    ADD_TEMP_MEDIA(state, { phase_index, step_index, media }) {
      let phase = state.temp[phase_index]
      let step = phase.steps[step_index]
      step.media.push(media)
    },

    DELETE_SAVED_MEDIA(state, { phase_index, step_index, index }) {
      let phase = state.temp[phase_index]
      let step = phase.steps[step_index]
      let media = step.media[index]
      media.trash = true
    },

    RESTORE_SAVED_MEDIA(state, { phase_index, step_index, index }) {
      let phase = state.temp[phase_index]
      let step = phase.steps[step_index]
      let media = step.media[index]
      media.trash = false
    },

    DELETE_TEMP_MEDIA(state, { phase_index, step_index, index }) {
      let phase = state.temp[phase_index]
      let media_list = phase.steps[step_index].media
      media_list.splice(index, 1)
    },

    ADD_OR_UPDATE_STEP(state, { phase_index, step_index, step_data}) {
      let procedure = state.temp[phase_index].steps
      procedure[step_index] = step_data
    },

    DELETE_STEP(state, { phase_index, step_index }) {
      let temp_procedure = state.temp[phase_index].steps
      temp_procedure.splice(step_index, 1)
    },

    DELETE_PHASE(state, phase_index) {
      state.temp.splice(phase_index, 1)
    },

    LOAD_OPERATIONS(state, op_list) {
      state.operations = op_list
    },

    CANCEL_PROCESS_CHANGES(state) {
      state.temp = _cloneDeep(state.saved)
    }
  },

  actions: {
    getOperations({commit}) {
      return new Promise( resolve => {
        api
        .get('operation')
        .then(resp => {
          commit('LOAD_OPERATIONS', resp.data)
          resolve()
        })
      }) 
    },

    createOperation({ dispatch }, new_operation_data) {
      return new Promise(resolve => {
        api
        .post(`operation`, new_operation_data)
        .then( async (resp) => {
          const new_op_key = resp.data.detail._key
          await dispatch('getOperations')
          resolve(new_op_key)
        })
      })
    },

    updateOperation({ dispatch }, { key, update }) {
      return new Promise( resolve => {
        api
        .patch(`operation/${key}`, update)
        .then( async () => {
          await dispatch('getOperations')
          resolve()
        })
      })
    },

    
    async getProcess({ commit }, product_key) {
      function get_step_media(step) {
        return new Promise( resolve => {
          api
          .get(`step/${step._key}/media`)
          .then( resp => {
            const media_list = resp.data.map( filename => {
              return {
                filename,
                src: `/media/step/${step._key}/${filename}`,
                temp: false,
                trash: false
              }
            })
            step.media = media_list
            resolve(step)
          })
        })
      }

      return new Promise( (resolve) => {
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
          resolve() 
        })
      }) 
    },

    saveTempProcess({ dispatch }, data) {
      return new Promise( (resolve, reject) => {

        // map added/deleted media
        let new_media = []
        let deleted_media = []

        data.new_process.forEach( phase => {
          phase.steps.forEach( step => {
            
            if (typeof step.media == 'undefined') return

            step.media.forEach( media => {
              if (media.trash) deleted_media.push({
                step_key: step._key,
                filename: media.filename
              })

              if (media.temp) new_media.push({
                step_key: step._key,
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

        // update process & product data
        axios.all(api_calls)
        .then(async () => {
          await axios.all([
            dispatch('getProcess', data.product_key),
            dispatch('loadProductDetails', data.product_key)
          ])
          resolve()
        })
        .catch(err => reject(err))
      })
    }
  },
}

export default process
