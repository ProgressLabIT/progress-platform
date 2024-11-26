import { api } from '@/boot/axios.js';

const warehouse = {
  state: {
    positions: [],
  },

  getters: {
    getPositionCount: (state) => () => {
      return state.positions.length;
    },
  },
  mutations: {
    LOAD_POSITIONS(state, positions) {
      state.positions = positions;
    },
    APPEND_POSITIONS(state, positions) {
      if (state.positions) {
        for (const position of positions) {
          state.positions.push(position);
        }
      } else {
        state.positions = positions;
      }
    },
  },

  actions: {
    async getPositions({ commit }, search_params) {
      const { data } = await api.get('position', { params: search_params });
      commit('LOAD_POSITIONS', data);
    },
    async appendPositions({ commit }, search_params) {
      const { data } = await api.get('position', { params: search_params });
      commit('APPEND_POSITIONS', data);
    },
  },
};

export default warehouse;
