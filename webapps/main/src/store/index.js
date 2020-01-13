import Vue from "vue";
import Vuex from "vuex";

Vue.use(Vuex);

import { updateListItemByKey as updateProduct } from '@/lib/ListUpdate.js'
import axios from 'axios'


export default new Vuex.Store({
  
  state() {
    return {
      products: [
        // {
        //   _key: 1,
        //   code: 'AAA123',
        //   description: 'This is a sample product card is a sample product card This is This is a sample product card is a sample product card This is a a sample product',
        //   active: true,
        //   trash: true
        // },
        // {
        //   _key: 2,
        //   code: 'BBB123',
        //   description: 'This is a sample product card',
        //   active: false,
        //   trash: false
        // },
        // {
        //   _key: 3,
        //   code: 'CCC123',
        //   description: 'This is a sample product card',
        //   active: true,
        //   trash: false
        // },
        // {
        //   _key: 4,
        //   code: 'DDD123',
        //   description: 'This is a sample product card',
        //   active: true,
        //   trash: false
        // },
        // {
        //   _key: 5,
        //   code: 'EEE123',
        //   description: 'This is a sample product card',
        //   active: true,
        //   trash: false
        // },
        // {
        //   _key: 6,
        //   code: 'FFF123',
        //   description: 'This is a sample product card',
        //   active: true,
        //   trash: false
        // },
      ]
    }
  },

  getters: {
    productList: state => () => {
      return state.products
    },

    notInTrash: state => () => {
      return state.products.filter( p => !p.trash )
    },
  },

  mutations: {
    // SWTICH_ACTIVE_STATE(state, key) {
    //   updateProduct(state.products, key, product => {
    //     Vue.set(product, 'active', !product.active)
    //   }) 
    // },

    // MOVE_TO_TRASH(state, key) {
    //   updateProduct(state.products, key, product => {
    //     Vue.set(product, 'trash', true)
    //   }) 
    // },

    // RESTORE_PRODUCT(state, key) {
    //   updateProduct(state.products, key, product => {
    //     Vue.set(product, 'trash', false)
    //   }) 
    // },

    UPDATE_PRODUCT(state, updated_product) {
      console.log({updated_product})
      updateProduct(state.products, updated_product._key, product => {
        for (const field in product) {
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
    }
  },

  actions: {
    switchActiveState({ commit }, product) {
      axios({
        method: 'patch',
        url: `http://127.0.0.1:8000/product/${product._key}`,
        data: { active: !product.active }
      })
      .then( resp => {
        // commit('SWTICH_ACTIVE_STATE', product._key)
        commit('UPDATE_PRODUCT', resp.data.detail )
      })
    },

    moveToTrash({ commit }, product) {
      // commit('MOVE_TO_TRASH', product._key)
      axios({
        method: 'patch',
        url: `http://127.0.0.1:8000/product/${product._key}`,
        data: { trash: true }
      })
      .then( resp => {
        commit('UPDATE_PRODUCT', resp.data.detail )
      }) 
    },

    restoreProduct({ commit }, productKey) {
      // commit('RESTORE_PRODUCT', productKey)
      axios({
        method: 'patch',
        url: `http://127.0.0.1:8000/product/${productKey}`,
        data: { trash: false }
      })
      .then( resp => {
        commit('UPDATE_PRODUCT', resp.data.detail )
      })
    },

    addNewProduct({ commit }, newProductData) {
      commit('ADD_NEW_PRODUCT', newProductData)
    },

    loadProductList({ commit }) {
      axios({
        method: 'get', 
        url: 'http://127.0.0.1:8000/product/'
      })
      .then(resp => {
        console.log(resp)
        const productList = resp.data
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
    }
  },

  modules: {}
});
