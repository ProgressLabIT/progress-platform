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
    UPDATE_SERIALS(state, serials) {
      let temp_serials = state.serials;
      if (serials) {
        for (const serial of serials) {
          temp_serials = temp_serials.map((item) =>
            item._key !== serial._key ? item : serial,
          );
        }
      }
      state.serials = temp_serials;
    },
    APPEND_SERIALS(state, serials) {
      if (!state.serials) {
        state.serials = serials;
        return;
      }

      for (const serial of serials) {
        if (!state.serials.some(s => s._key === serial._key)) {
          state.serials.push(serial);
        }
      }
    },
    LOAD_SERIAL_FIELDS(state, serial_fields) {
      state.serial_fields = serial_fields;
    },
    SET_ROUND(state, loading_round) {
      state.loading_round = loading_round;
    },
  },

  actions: {
    async getSerials({ commit }, search_params) {
      const { data } = await api.get('serial', { params: search_params });
      commit('LOAD_SERIALS', data);
    },
    async updateSerials({ commit }, search_params) {
      const { data } = await api.get('serial', { params: search_params });
      commit('UPDATE_SERIALS', data);
    },
    async appendSerials({ commit }, search_params) {
      const { data } = await api.get('serial', { params: search_params });
      commit('APPEND_SERIALS', data);
    },
    async getSerialFields({ commit }) {
      const { data } = await api.get('serial-field');
      commit('LOAD_SERIAL_FIELDS', data);
    },
    async appendSerial({ commit }, search_params) {
      const { data } = await api.get('serial', { params: search_params });
      commit('APPEND_SERIALS', data);
      return data[0];
    },
  },
};

export default serial;
