import Vue from "vue";
import Vuex from "vuex";

Vue.use(Vuex);

import { updateListItemByKey as updateProduct } from '@/lib/ListUpdate.js'

export default new Vuex.Store({
  
  state() {
    return {
      products: [
        {
          _key: 1,
          code: 'AAA123',
          description: 'This is a sample product card is a sample product card This is This is a sample product card is a sample product card This is a a sample product',
          active: true,
          trash: true
        },
        {
          _key: 2,
          code: 'BBB123',
          description: 'This is a sample product card',
          active: false,
          trash: false
        },
        {
          _key: 3,
          code: 'CCC123',
          description: 'This is a sample product card',
          active: true,
          trash: false
        },
        {
          _key: 4,
          code: 'DDD123',
          description: 'This is a sample product card',
          active: true,
          trash: false
        },
        {
          _key: 5,
          code: 'EEE123',
          description: 'This is a sample product card',
          active: true,
          trash: false
        },
        {
          _key: 6,
          code: 'FFF123',
          description: 'This is a sample product card',
          active: true,
          trash: false
        },
      ]
    }
  },

  getters: {
    notInTrash: state => () => {
      return state.products.filter( p => !p.trash )
    },
  },

  mutations: {
    SWTICH_ACTIVE_STATE(state, key) {
      updateProduct(state.products, key, product => {
        console.log('Changing active state for product key: ' + key)
        console.log('Previous state: ' + product.active)
        console.log('New state: ' + !product.active)
        Vue.set(product, 'active', !product.active)
      }) 
    }
  },

  actions: {
    switchActiveState({ commit }, productKey) {
      commit('SWTICH_ACTIVE_STATE', productKey)
    }
  },

  modules: {}
});
