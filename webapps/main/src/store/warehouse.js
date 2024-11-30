import { cloneDeep as _cloneDeep } from 'lodash';
import { api } from '@/boot/axios.js';

const warehouse = {
  state: {
    positions: [],
    temp_print_templates: [],
    saved_print_templates: [],
    position_search_params: undefined,
  },

  getters: {
    getPositionCount: (state) => () => {
      return state.positions.length;
    },
    getPositionData: (state) => (position_key) => {
      return state.positions.find((i) => i._key == position_key);
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

    SET_POSITION_SEARCH_PARAMS(state, params) {
      state.position_search_params = params;
    },

    ADD_TEMP_LABEL_PRINT_TEMPLATE(state, template) {
      state.temp_print_templates.push({ ...template, temp: true });
    },

    DELETE_TEMP_LABEL_PRINT_TEMPLATE(state, template_index) {
      state.temp_print_templates.splice(template_index, 1);
    },

    SET_LABEL_PRINT_TEMPLATE(state, templates) {
      state.temp_print_templates = _cloneDeep(templates);
      state.saved_print_templates = _cloneDeep(templates);
    },

    RESET_LABEL_PRINT_TEMPLATE(state) {
      state.temp_print_templates = [];
      state.saved_print_templates = [];
    },
  },

  actions: {
    async getPositions({ commit }, search_params) {
      const { data } = await api.get('position', { params: search_params });
      commit('LOAD_POSITIONS', data);
      commit('SET_POSITION_SEARCH_PARAMS', search_params);
    },

    async appendPositions({ commit }, search_params) {
      const { data } = await api.get('position', { params: search_params });
      commit('APPEND_POSITIONS', data);
      commit('SET_POSITION_SEARCH_PARAMS', search_params);
    },

    async postPositions({ state, dispatch }, positions) {
      await Promise.all(
        positions.map((position) => api.post('position', position)),
      );
      await dispatch('getPositions', state.position_search_params);
    },

    loadPrintLabelTemplates({ commit }) {
      api
        .get('print-template', {
          params: { context: 'position', context_key: 'IN' },
        })
        .then((resp) => {
          if (resp && resp?.data) {
            commit('SET_LABEL_PRINT_TEMPLATE', resp.data);
          } else {
            commit('SET_LABEL_PRINT_TEMPLATE', []);
          }
        });
    },
    savePrintTemplates({ commit }, params) {
      if (params.deleted_templates != null || params.new_templates != null) {
        const template_updates = [
          ...params.deleted_templates.map((t) => ({
            type: 'remove',
            context: 'position',
            context_key: 'IN',
            template_key: t._key,
          })),
          ...params.new_templates.map((t) => ({
            type: 'add',
            context: 'position',
            context_key: 'IN',
            template_key: t._key,
          })),
        ];
        commit('RESET_LABEL_PRINT_TEMPLATE');

        api.post('update-template-assignments', template_updates).then(() => {
          api
            .get('print-template', {
              params: { context: 'position', context_key: 'IN' },
            })
            .then((resp) => {
              if (resp && resp?.data) {
                commit('SET_LABEL_PRINT_TEMPLATE', resp.data);
              } else {
                commit('SET_LABEL_PRINT_TEMPLATE', []);
              }
            });
        });
      }
    },
  },
};

export default warehouse;
