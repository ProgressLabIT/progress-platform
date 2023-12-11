import { api } from '@/boot/axios.js';

const bom = {
  state: {
    saved: [],
    temp: [],
  },

  mutations: {
    LOAD_SAVED_BOM(state, bom) {
      state.saved = [...bom];
      state.temp = [...bom];
    },

    UPDATE_TEMP_BOM(state, new_bom) {
      state.temp = new_bom;
    },
  },

  actions: {
    saveBomChanges({ dispatch }, { product_key, new_bom }) {
      return new Promise((resolve, reject) => {
        api
          .put(`product/${product_key}/bom`, new_bom)
          .then(() => {
            dispatch('getBom', product_key);
            resolve();
          })
          .catch((err) => reject(err));
      });
    },

    getBom({ commit }, product_key) {
      api.get(`product/${product_key}/bom`).then((resp) => {
        commit('LOAD_SAVED_BOM', resp.data);
      });
    },
  },
};

export default bom;
