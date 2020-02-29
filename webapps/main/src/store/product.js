import Vue from "vue"
import { cloneDeep as _cloneDeep } from 'lodash'
import { api } from '@/lib/apiCall.js'
import { updateListItemByKey as updateProduct } from '@/lib/ListUpdate.js' 
// import { durationFromMillisec as duration } from '@/lib/duration.js'

const product = {

  state: {
    saved: {},
    temp: {},
    list: []
  },

  mutations: {
    UPDATE_PRODUCT(state, updated_product) {
      // console.log({updated_product})
      updateProduct(state.list, updated_product._key, product => {
        for (const field in updated_product) {
          if (field != '_key') {
            Vue.set(product, field, updated_product[field])
          }
        }
      })
    },

    /**
     * The mutation below is the exact copy of the one above. 
     * The duplication is to semantically separate the update
     * of fields that do not need backend sync from those that do
     */
    UPDATE_PRODUCT_NAV_STATE(state, updated_product) {
      updateProduct(state.list, updated_product._key, product => {
        for (const field in updated_product) {
          if (field != '_key') {
            Vue.set(product, field, updated_product[field])
          }
        }
      })
    },

    UPDATE_TEMP_PARAMETER(state, { param, new_value }) {
      Vue.set(state.temp, param, new_value)
    },

    UPDATE_TEMP_TARGET(state, { param, new_target} ) {
      Vue.set(state.temp[param], 'target', new_target)
    },

    ADD_NEW_PRODUCT(state, new_product_data) {
      state.list.push(new_product_data)
    },

    LOAD_PRODUCT_LIST(state, product_list) {
      Vue.set(state, 'list', product_list)
    },

    LOAD_PRODUCT_DETAILS(state, product_details) {
      Vue.set(state, 'saved', _cloneDeep(product_details))
      Vue.set(state, 'temp', _cloneDeep(product_details))      
    },

    // SAVE_PRODUCT_CHANGES(state, updated_product) {
    //   Vue.set(state, 'saved', _cloneDeep(updated_product))
    //   Vue.set(state, 'temp', _cloneDeep(updated_product))
    // },

    CANCEL_PRODUCT_CHANGES(state) {
      Vue.set(state, 'temp', _cloneDeep(state.saved))
    }
  },

  actions: {
    switchActiveState({ commit }, product) {
      api.patch(
        `product/${product._key}`,
        { active: !product.active }
      )
      .then( resp => {
        // commit('SWTICH_ACTIVE_STATE', product._key)
        commit('UPDATE_PRODUCT', resp.data.detail )
      })
    },

    moveToTrash({ commit }, product) {
      api.patch(
        'product/' + product._key,
        { trash: true }
      )
      .then( resp => {
        commit('UPDATE_PRODUCT', resp.data.detail )
      }) 
    },

    restoreProduct({ commit }, product_key) {
      api.patch(
        'product/' + product_key,
        { trash: false }
      )
      .then( resp => {
        commit('UPDATE_PRODUCT', resp.data.detail )
      })
    },

    loadProductList({ commit }) {
      api.get('product')
        .then(resp => {
          // console.log(resp)
          const productList = resp.data
          productList.forEach( p => {
            p.last_page = 'home'
            // p.last_process_tab = 0
            p.last_phase = 0,
            p.last_steps = [0]
          })
          commit('LOAD_PRODUCT_LIST', productList)
        })
        .catch(error => {        
          window.alert(`Couldn't fetch data from db. Error:\n ${error}`)
        })
    },

    loadProductDetails({ commit }, product_key) {
      api.get(`product/${product_key}`)
        .then( resp => {
          commit('LOAD_PRODUCT_DETAILS', resp.data)
        })
    },


    saveProductChanges({ commit }, data) {
      return new Promise ( resolve => {
        api
          .put(`product/${data.product_key}`, data.new_product_data)
          .then( resp => {
            commit('LOAD_PRODUCT_DETAILS', resp.data)
            resolve()
          })
        })
    },

  },

  getters: {
    productList: (state) => () => {
      return state.list
    },

    notInTrash: (state) => () => {
      return state.list.filter( p => !p.trash )
    },

    productData: (state) => (product_key) => {
      return state.list.find( p => p._key == product_key)
    }
  }
}

export default product