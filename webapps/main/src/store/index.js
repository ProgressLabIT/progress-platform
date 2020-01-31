import Vue from "vue";
import Vuex from "vuex";
import axios from 'axios';

Vue.use(Vuex);

import { updateListItemByKey as updateProduct } from '@/lib/ListUpdate.js'
// import axios from 'axios'
import { api } from '@/lib/apiCall.js'


export default new Vuex.Store({
  
  state() {
    return {
      products: [],
      current_product: { 
        metadata: {},
        process: [], 
        bom: [],     
        issues: [],  
        docs: []          // { name, size, type }
      }
    }
  },

  getters: {
    productList: state => () => {
      return state.products
    },

    notInTrash: state => () => {
      return state.products.filter( p => !p.trash )
    },

    productData: state => (product_key) => {
      return state.products.find( p => p._key == product_key)
    }
  },

  mutations: {

    UPDATE_PRODUCT(state, updated_product) {
      // console.log({updated_product})
      updateProduct(state.products, updated_product._key, product => {
        for (const field in updated_product) {
          if (field != '_key') {
            Vue.set(product, field, updated_product[field])
          }
        }
      })
    },

    ADD_NEW_PRODUCT(state, newProductData) {
      state.products.push(newProductData)
    },

    LOAD_PRODUCT_LIST(state, productList) {

      Vue.set(state, 'products', productList)
    },

    LOAD_PRODUCT_DETAILS(state, productDetails) {
      /* 
       *  Currently this only sets the product metadata.
       *  Data about process, bom, issues must be added.
       */
      Vue.set(state, 'current_product', productDetails)
    },

      /**
       * Use this mutation to add, remove
       * change sequence of process phases
       */
    UPDATE_PROCESS(state, process) {
      Vue.set(state.current_product, 'process', process)
    },

    UPDATE_PROCEDURE(state, { phase_no, procedure }) {
      Vue.set(state.current_product.process[phase_no], 'steps', procedure)
    },

    UPDATE_STEP_DETAILS(state,  { phase_no, step_no, field, value })  {
      let process = state.current_product.process
      let phase = process[phase_no]
      let step = phase.steps[step_no]
      Vue.set(step, field, value)
    },

    ADD_OR_UPDATE_STEP(state, { phase_no, step_no, step_data}) {
      let process = state.current_product.process
      let procedure = process[phase_no].steps
      Vue.set(procedure, step_no, step_data)
    },

    DELETE_STEP(state, { phase_no, step_no }) {
      let procedure = state.current_product.process[phase_no].steps
      procedure.splice(step_no, 1)
    },

    DELETE_PHASE(state, phase_no) {
      let process = state.current_product.process
      process.splice(phase_no, 1)
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
          const fake_db = [
            {
              _key: 1,
              code: 'SAMPLE1',
              description: 'This is a sample product card is a sample product card This is This is a sample product card is a sample product card This is a a sample product',
              active: true,
              trash: true
            },
            {
              _key: 2,
              code: 'SAMPLE2',
              description: 'This is a sample product card',
              active: false,
              trash: false
            },
            {
              _key: 3,
              code: 'SAMPLE3',
              description: 'This is a sample product card',
              active: true,
              trash: false
            },
            {
              _key: 4,
              code: 'SAMPLE4',
              description: 'This is a sample product card',
              active: true,
              trash: false
            },
            {
              _key: 5,
              code: 'SAMPLE5',
              description: 'This is a sample product card',
              active: true,
              trash: false
            },
            {
              _key: 6,
              code: 'SAMPLE6',
              description: 'This is a sample product card',
              active: true,
              trash: false
            },
          ]

          window.alert(`Couldn't fetch data from db. Loading sample products\nError: ${error}`)
          commit('LOAD_PRODUCT_LIST', fake_db)
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

  modules: {}
});
