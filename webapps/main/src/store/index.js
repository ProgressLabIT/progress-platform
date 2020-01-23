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
        process: [
          // { 
          //   operation: 'picking',
          //   steps: [
          //     { title: '1Primo step', description: 'prova di procedura', type: 'instruction' },
          //     { title: '1Secondo step', description: 'prova di procedura', type: 'checklist' },
          //     { title: '1Terzo step', description: 'prova di procedura', type: 'instruction' },
          //     { title: '1Quarto step', description: 'prova di procedura', type: 'instruction' },
          //     { title: '1Quinto step', description: 'prova di procedura', type: 'form' },
          //     { title: '1Sesto step', description: 'prova di procedura', type: 'form' },
          //     { title: '1Settimo step', description: 'prova di procedura', type: 'checklist' },

          //   ]
          // },
          // { 
          //   operation: 'assembly',
          //   steps: [
          //     { title: '2Primo step', description: 'prova di procedura', type: 'instruction' },
          //     { title: '2Secondo step', description: 'prova di procedura', type: 'checklist' },
          //     { title: '22Terzo step', description: 'prova di procedura', type: 'instruction' },
          //     { title: 'Q2uarto step', description: 'prova di procedura', type: 'instruction' },
          //     { title: 'Q2uinto step', description: 'prova di procedura', type: 'form' },
          //     { title: 'S2esto step', description: 'prova di procedura', type: 'form' },
          //     { title: 'S2ettimo step', description: 'prova di procedura', type: 'checklist' },
          //   ]
          // },
          // { 
          //   operation: 'testing',
          //   steps: [
          //     { title: 'Primo step', description: 'prova di procedura', type: 'instruction' },
          //     { title: 'Secondo step', description: 'prova di procedura', type: 'checklist' },
          //     { title: 'Terzo step', description: 'prova di procedura', type: 'instruction' },
          //     { title: 'Quarto step', description: 'prova di procedura', type: 'instruction' },
          //     { title: 'Quinto step', description: 'prova di procedura', type: 'form' },
          //     { title: 'Sesto step', description: 'prova di procedura', type: 'form' },
          //     { title: 'Settimo step', description: 'prova di procedura', type: 'checklist' },
          //   ]
          // },
          // { 
          //   operation: 'shipping',
          //   steps: [
          //     { title: '3Primo step', description: 'prova di procedura', type: 'instruction' },
          //     { title: '3Secondo step', description: 'prova di procedura', type: 'checklist' },
          //     { title: '3Terzo step', description: 'prova di procedura', type: 'instruction' },
          //     { title: 'Q3uarto step', description: 'prova di procedura', type: 'instruction' },
          //     { title: '3Quinto step', description: 'prova di procedura', type: 'form' },
          //     { title: '3Sesto step', description: 'prova di procedura', type: 'form' },
          //     { title: '3Settimo step', description: 'prova di procedura', type: 'checklist' },
          //   ]
          // }
        ], // list of phases
        bom: [
          // { code: 'K100-25-014', description: 'SPALLA SX ASSE Y ACS2000', qt: 1, unit: 'pcs', type: 'assembly' },
          // { code: 'K100-71-132', description: 'PIASTRA FERMO CINGHIA PER REGISTRO ASSE Y ACS1500/2000', qt: 2, unit: 'pcs', type: 'assembly' },
          // { code: 'S100-27-034', description: 'BLOCCHETTO REGOLAZIONE ASSE Y 1500/2000', qt: 2, unit: 'pcs', type: 'component' },
          // { code: 'S100-27-041', description: 'GUIDA LINEARE ASSE Y SMD1500', qt: 2, unit: 'pcs', type: 'component' },
          // { code: 'S100-27-055', description: 'TENDI CINGHIA MOTORE ASSE Y TETTO ACS1100', qt: 1, unit: 'pcs', type: 'assembly' },
          // { code: 'S100-42-053', description: 'RUOTE CONCENTRICHE D=30 ACCIAIO C208 135', qt: 4, unit: 'pcs', type: 'component' },
          // { code: 'S100-42-055', description: 'CINGHIA T10 L=16HF POLIETILENE CON ANIMA ACCIAIO', qt: 5, unit: 'pcs', type: 'component' },
          // { code: 'S300-01-020', description: 'CAVO KONTEK ASSE Y BK34010422CTM', qt: 1, unit: 'pcs', type: 'assembly' },
          // { code: 'K100-25-013', description: 'SPALLA DX ASSE Y + ACCUM. ACS2000', qt: 2, unit: 'm', type: 'component' },
          // { code: 'K100-25-016', description: 'CONTRAPPESO ACS 2000', qt: 2, unit: 'kg', type: 'component' },
          // { code: 'K100-71-134', description: 'STAFFA BLOCCA CINGHIA CONTRAP. ACS1500/2000', qt: 2, unit: 'pcs', type: 'component' },
          // { code: 'S100-27-036', description: 'ASTA CONTRAPPESO SMD1500', qt: 2, unit: 'pcs', type: 'component' },
          // { code: 'S100-27-042', description: 'CONTRAPPESO AGGIUNTIVO ACS2000', qt: 4, unit: 'lt', type: 'component' },
          // { code: 'S100-27-064', description: 'BOCCOLA PER CONTRAPPESO 1500/2000', qt: null, unit: '', type: 'consumable' },
          // { code: 'S100-42-054', description: 'RUOTE ECCENTRICHE D=30 ACCIAIO E208-135', qt: null, unit: '', type: 'consumable' },
          // { code: 'S100-73-026', description: 'PIASTRA SUPPORTO SCHEDA RESET SPINTORE 1500/2000 + ASSE X', qt: null, unit: '', type: 'consumable' },
        ],          // 
        issues: [],       // { }
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

    // UDPATE_PRODUCT_NAV_STATE(state, product_key, item, value) {
    //   updateProduct(state.products, product_key, product => {
    //     Vue.set(product, item, value)
    //   })
    // }

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

  },

  actions: {
    switchActiveState({ commit }, product) {
      // axios({
      //   method: 'patch',
      //   url: `http://127.0.0.1:8000/product/${product._key}`,
      //   data: { active: !product.active }
      // })
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
      // commit('MOVE_TO_TRASH', product._key)
      // axios({
      //   method: 'patch',
      //   url: `http://127.0.0.1:8000/product/${product._key}`,
      //   data: { trash: true }
      // })
      api.patch(
        'product/' + product._key,
        { trash: true }
      )
      .then( resp => {
        commit('UPDATE_PRODUCT', resp.data.detail )
      }) 
    },

    restoreProduct({ commit }, product_key) {
      // commit('RESTORE_PRODUCT', product_key)
      // axios({
      //   method: 'patch',
      //   url: `http://127.0.0.1:8000/product/${product_key}`,
      //   data: { trash: false }
      // })
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
      // axios({
      //   method: 'get', 
      //   url: 'http://127.0.0.1:8000/product/'
      // })
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
        commit('LOAD_PRODUCT_DETAILS', {
          metadata: meta.data,
          bom: bom.data,
          process: process.data
        })
      }))

      //  api.get(`product/${product_key}`)
      //   .then( resp => { 
      //     commit('LOAD_PRODUCT_DETAILS', { metadata: resp.data })
      //   })
      
      // api.get(`product/${product_key}/bom`)
      //   .then( resp => {
      //     commit('LOAD_PRODUCT_DETAILS', { bom: resp.data })
      //   })

      // api.get(`product/${product_key}/process`)
      //   .then( resp => {
      //     commit('LOAD_PRODUCT_DETAILS', { process: resp.data })
      //   })
    }
  },

  modules: {}
});
