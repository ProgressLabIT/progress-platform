import { defineStore } from 'pinia';
import { api } from '@/boot/axios';
import { store } from '@/boot/store.js';

export const useCountingStore = defineStore('counting', {
  state: () => ({
    sessionData: null,
    countedItems: {},
    tempSerials: [],
  }),
  actions: {
    async loadCountSessionData(countSessionKey) {
      const response = await api.get(`/inventory/count-session/${countSessionKey}`, {
        params: {
          user_key: store.getters.getUserKey,
        },
      });
      this.sessionData = response.data;
    },
    saveCount(countData) {
      const dataToLog = {
        inventory_key: countData.inventory_key,
        product_key: countData.product_key,
        position_key: countData.position_key,
        serial_key: countData.serial_key || null,
        quantity_original: countData.quantity_original,
        quantity_counted: countData.quantity_counted,
        serials_counted: countData.serials_counted || [],
        timestamp: new Date().toISOString(),
      };
      console.log('Count data saved:', dataToLog);

      // Store in countedItems
      this.countedItems[countData.inventory_key] = dataToLog;
    },
    resetCounting() {
      this.countedItems = {};
      this.tempSerials = [];
    }
  }
});
