import { defineStore } from 'pinia';
import { api } from '@/boot/axios';

export const useInventoryStore = defineStore('inventory', {
  state: () => ({
    position: null,
    contents: [],
  }),
  actions: {
    async loadInventory(params) {
      const response = await api.get('/inventory', { params });
      this.contents = response.data;
    },
    async loadPositionContents(position_key) {
      const response = await api.get(`/position/${position_key}`);
      this.contents = response.data;
    }
  }
});
