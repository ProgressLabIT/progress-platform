import { defineStore } from 'pinia';
import { api } from '@/boot/axios';
import { store } from '@/boot/store.js';
import { sendEvent } from '@/composables/event';


export const useCountingStore = defineStore('counting', {
  state: () => ({
    sessionData: null,
    tempSerials: [],
    selectedPosition: null,
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
    /**
     * Complete a count record
     * Uses COUNT_COMPLETED event
     * @param {Object} countData - Count data object
     * @param {string} countData.count_key - The count record key to complete (required)
     * @param {number} countData.quantity_counted - The counted quantity (required)
     * @param {Array<string>} countData.serials_counted - Optional array of serial keys
     * @param {string} countData.notes - Optional notes
     * @returns {Promise<void>}
     */
    async saveCount(countData) {
      if (!countData.count_key) {
        throw new Error('count_key is required to complete a count');
      }

      await sendEvent({
        event_type: 'COUNT_COMPLETED',
        event_data: {
          count_key: countData.count_key,
          count_qt: countData.count_qt,
          count_serial_keys: countData.serials_counted || null,
          notes: countData.notes || null,
        }
      });
    },
    resetCounting() {
      this.tempSerials = [];
    },
    setSelectedPosition(position) {
      this.selectedPosition = position;
    },
    resetPositionNavigation() {
      this.selectedPosition = null;
    }
  }
});
