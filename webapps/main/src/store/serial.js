import { api } from '@/boot/axios.js';

const serial = {
  state: {
    serials: [],
  },

  getters: {
    getSerialData: (state) => (serial_key) => {
      return state.serials.find((i) => i._key == serial_key);
    },
    getSerialCount: (state) => () => {
      return state.serials.length;
    },
  },

  mutations: {
    LOAD_SERIALS(state, serials) {
      state.serials = serials;
    },
  },

  actions: {
    async getSerials({ commit }, search_params) {
      const { data } = await api.get('serial', { params: search_params });
      commit('LOAD_SERIALS', data);
    },
  },
};

export default serial;
