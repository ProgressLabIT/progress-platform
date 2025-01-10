import { cloneDeep as _cloneDeep } from 'lodash';
import { api } from '@/boot/axios.js';
import { Notify } from 'quasar';

const warehouse = {
  state: {
    positions: [],
    temp_print_templates: [],
    saved_print_templates: [],
    position_search_params: undefined,
    movements: [],
    movement_search_params: undefined,
    inventory: [],
    inventory_search_params: undefined,
  },

  getters: {
    getPositionCount: (state) => () => {
      return state.positions.length;
    },
    getPositionData: (state) => (position_key) => {
      return state.positions.find((i) => i._key == position_key);
    },

    getMovementCount: (state) => () => {
      return state.movements.length;
    },
    getMovementData: (state) => (movement_key) => {
      return state.movements.find((i) => i._key == movement_key);
    },

    getInventoryCount: (state) => () => {
      return state.inventory.length;
    },
    getInventoryData: (state) => (inventory_key) => {
      return state.inventory.find((i) => i._key == inventory_key);
    },
  },
  mutations: {
    // POSITION
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

    // POSITION PRINT LABEL
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

    // MOVEMENT
    LOAD_MOVEMENTS(state, movements) {
      state.movements = movements;
    },
    APPEND_MOVEMENTS(state, movements) {
      if (state.movements) {
        for (const movement of movements) {
          state.movements.push(movement);
        }
      } else {
        state.movements = movements;
      }
    },
    SET_MOVEMENT_SEARCH_PARAMS(state, params) {
      state.movement_search_params = params;
    },

    // INVENTORY
    LOAD_INVENTORY(state, inventory) {
      state.inventory = inventory;
    },
    APPEND_INVENTORY(state, inventory) {
      if (state.inventory) {
        for (const inv of inventory) {
          state.inventory.push(inv);
        }
      } else {
        state.inventory = inventory;
      }
    },
    SET_INVENTORY_SEARCH_PARAMS(state, params) {
      state.inventory_search_params = params;
    },

    // MOVEMENT LIST
    LOAD_MOVEMENT_LISTS(state, movement_lists) {
      state.movement_lists = movement_lists;
    },
    APPEND_MOVEMENT_LISTS(state, movement_lists) {
      state.movement_lists.push(...movement_lists);
    },
    SET_MOVEMENT_LIST_SEARCH_PARAMS(state, params) {
      state.movement_list_search_params = params;
    },
  },

  actions: {
    // POSITIONS
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

    // PRINT LABELS

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

    // MOVEMENTS
    async getMovements({ commit }, search_params) {
      try {
        const { data } = await api.get('movement', { params: search_params });
        commit('LOAD_MOVEMENTS', data);
        commit('SET_MOVEMENT_SEARCH_PARAMS', search_params);
      } catch (error) {
        Notify.create({
          message: error.message,
          color: 'theme-red',
          timeout: 1500,
          position: 'top',
        });
      }
    },

    async appendMovements({ commit }, search_params) {
      const { data } = await api.get('movement', { params: search_params });
      commit('APPEND_MOVEMENTS', data);
      commit('SET_MOVEMENT_SEARCH_PARAMS', search_params);
    },

    // INVENTORY
    async getInventory({ commit }, search_params) {
      const { data } = await api.get('inventory', { params: search_params });
      commit('LOAD_INVENTORY', data);
      commit('SET_INVENTORY_SEARCH_PARAMS', search_params);
    },

    async appendInventory({ commit }, search_params) {
      const { data } = await api.get('inventory', { params: search_params });
      commit('APPEND_INVENTORY', data);
      commit('SET_INVENTORY_SEARCH_PARAMS', search_params);
    },

    async getMovementLists({ commit }, search_params) {
      const { data } = await api.get('movement-list', { params: search_params });
      commit('LOAD_MOVEMENT_LISTS', data);
      commit('SET_MOVEMENT_LIST_SEARCH_PARAMS', search_params);
    },

    async appendMovementLists({ commit }, search_params) {
      const { data } = await api.get('movement-list', { params: search_params });
      commit('APPEND_MOVEMENT_LISTS', data);
      commit('SET_MOVEMENT_LIST_SEARCH_PARAMS', search_params);
    },
  },
};

export default warehouse;
