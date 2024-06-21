import { api } from '@/boot/axios.js';

const serial = {
  state: {
    serials: [],
    serial_fields: [],
  },

  getters: {
    getSerialData: (state) => (serial_key) => {
      return state.serials.find((i) => i._key == serial_key);
    },
    getSerialCount: (state) => () => {
      return state.serials.length;
    },
    getSerialFields: (state) => () => {
      return state.serial_fields;
    },
  },

  mutations: {
    LOAD_SERIALS(state, serials) {
      state.serials = serials;
    },
    LOAD_SERIAL_FIELDS(state, serial_fields) {
      state.serial_fields = serial_fields;
    },
  },

  actions: {
    async getSerials({ commit }, search_params) {
      const { data } = await api.get('serial', { params: search_params });
      commit('LOAD_SERIALS', data);
    },
    async getSerialFields({ commit }) {
      const { data } = await api.get('serial-field');
      commit('LOAD_SERIAL_FIELDS', data);
    },
  },
};

export default serial;
