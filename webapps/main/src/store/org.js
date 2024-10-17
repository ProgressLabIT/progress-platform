import { api } from '@/boot/axios.js';

const org = {
  state: {
    departments: [],
    wo_open_proucts: [],
    wo_open_codes: [],
    wo_open_phases: [],
  },

  mutations: {
    LOAD_DEPARTMENTS(state, dep_list) {
      state.departments = dep_list;
    },

    LOAD_WO_OPEN_PRODUCTS(state, product_list) {
      state.wo_open_proucts = product_list;
    },

    LOAD_WO_OPEN_CODES(state, code_list) {
      state.wo_open_codes = code_list;
    },

    LOAD_WO_OPEN_PHASES(state, phase_list) {
      state.wo_open_phases = phase_list;
    },
  },

  actions: {
    loadDepartments({ commit }) {
      return new Promise((resolve) => {
        api.get('department').then((resp) => {
          commit('LOAD_DEPARTMENTS', resp.data.detail);
          resolve();
        });
      });
    },

    loadWorkOrderSearchOptions({ commit }) {
      return new Promise((resolve) => {
        api.get('work-order-search-opts').then((resp) => {
          commit('LOAD_WO_OPEN_PRODUCTS', resp?.data[0]?.products);
          commit('LOAD_WO_OPEN_CODES', resp?.data[0]?.wo_codes);
          commit('LOAD_WO_OPEN_PHASES', resp?.data[0]?.phases);
          resolve();
        });
      });
    },
  },
};

export default org;
