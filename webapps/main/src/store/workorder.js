import { api } from '@/boot/axios.js';

const workorder = {
  state: {
    wo_map: {},
    temp_queue: [],
    saved_queue: [],
    wo_data: {},
  },

  mutations: {
    LOAD_WORK_ORDERS(state, list) {
      state.saved_queue = [];
      state.temp_queue = [];
      list.forEach((wo, index) => {
        state.wo_map[wo._key] = { ...wo, sequence: index + 1 };
        state.saved_queue.push(wo._key);
        state.temp_queue.push(wo._key);
      });
    },

    LOAD_WORK_ORDER_DATA(state, wo_data) {
      state.wo_data = wo_data;
    },

    UPDATE_WO_LIST(state, wo_updates) {
      wo_updates.forEach((wo, index) => {
        state.wo_map[wo._key] = {
          ...wo,
          sequence: index + 1,
        };
      });
    },

    SORT_TEMP_QUEUE_BY_START_DATE_DUE_DATE(state) {
      let temp_wo_list = [];
      state.temp_queue.forEach((key) => {
        temp_wo_list.push(state.wo_map[key]);
      });
      temp_wo_list.sort((a, b) => {
        var start_fromA = new Date(a.start_from),
          start_fromB = new Date(b.start_from);
        if (start_fromA < start_fromB) {
          return -1;
        }
        if (start_fromA > start_fromB) {
          return 1;
        }
        var due_byA = new Date(a.due_by),
          due_byB = new Date(b.due_by);
        if (due_byA < due_byB) {
          return -1;
        }
        if (due_byA > due_byB) {
          return 1;
        }
        return 0;
      });
      let new_queue = [];
      temp_wo_list.forEach((wo) => {
        new_queue.push(wo._key);
      });
      state.temp_queue = [...new_queue];
    },

    UPDATE_TEMP_QUEUE(state, { new_queue_index, old_queue_index }) {
      const selected_wo = state.temp_queue.splice(old_queue_index, 1)[0];
      state.temp_queue.splice(new_queue_index, 0, selected_wo);
    },

    RESET_TEMP_QUEUE(state) {
      state.temp_queue = [...state.saved_queue];
    },
  },

  actions: {
    async loadWorkOrders({ commit }) {
      const { data } = await api.get(`queue/site/0`);
      commit('LOAD_WORK_ORDERS', data.detail);
    },

    // Differs from the above because it doesn't change the queue
    async updateWorkOrderList({ commit }) {
      const { data } = await api.get(`queue/site/0`);
      commit('UPDATE_WO_LIST', data.detail);
    },

    async postWorkOrder({ dispatch }, workOrders) {
      await Promise.all(
        workOrders.map((workOrder) => api.post('work-order', workOrder)),
      );
      await dispatch('loadWorkOrders');
    },

    async loadWorkOrderData({ commit }, workOrderKey) {
      const { data } = await api.get(`work-order/${workOrderKey}`);
      commit('LOAD_WORK_ORDER_DATA', data.detail);
    },

    async updateWorkOrder(_, { wo_key, ...work_order_updates }) {
      await api.patch(`work-order/${wo_key}`, work_order_updates);
    },

    async updateWorkOrderQuantities(_, payload) {
      await api.patch(
        `work-order/${payload.wo_key}/update-quantities`,
        payload,
      );
    },

    async saveQueueChanges({ dispatch, state }) {
      const queue_update = {
        type: 's',
        // Use default site until full multi-site management is implemented
        site_key: '0',
        work_orders: state.temp_queue,
      };
      await api.put('queue', queue_update);
      await Promise.all([
        dispatch('loadWorkOrders'),
        dispatch('loadJobAssignments'),
      ]);
    },
  },
};

export default workorder;
