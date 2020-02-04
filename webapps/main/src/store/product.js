import Vue from "vue"
import axios from "axios"
import { api } from '@/lib/apiCall.js'
import { updateListItemByKey as updateProduct } from '@/lib/ListUpdate.js' 

const product = {

  state: {
    details: {},
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

    ADD_NEW_PRODUCT(state, newProductData) {
      state.list.push(newProductData)
    },

    LOAD_PRODUCT_LIST(state, product_list) {
      Vue.set(state, 'list', product_list)
    },

    LOAD_PRODUCT_DETAILS(state, product_details) {
      /* 
       *  Currently this only sets the product metadata.
       *  Data about process, bom, issues must be added.
       */
      Vue.set(state, 'details', product_details.metadata)
      Vue.set(this.state.process, 'phases', product_details.process)
      Vue.set(this.state.bom, 'items', product_details.bom)
    },
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

    addNewProduct({ commit }, newProductData) {
      commit('ADD_NEW_PRODUCT', newProductData)
    },

    loadProductList({ commit }) {
      api
        .get('product')
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
      axios.all([
          api.get(`product/${product_key}`),
          api.get(`product/${product_key}/bom`),
          api.get(`product/${product_key}/process`)
      ])
      .then(axios.spread((meta, bom, process) => {
        let product_details = {
          metadata: meta.data,
          bom: bom.data,
          process: process.data
        }
        // console.log("loading product details", product_details)
        commit('LOAD_PRODUCT_DETAILS', product_details)
      }))
    }

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