import { defineStore } from 'pinia';
import { api } from '@/boot/axios';
import { store } from '@/boot/store.js';
import { sendEvent } from '@/composables/event';
import { Notify } from 'quasar';


export const useCountingStore = defineStore('counting', {
  state: () => ({
    sessionData: null,
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
     * @param {number} countData.count_qt - The counted quantity (required)
     * @param {Array<string>} countData.count_serial_keys - Optional array of serial keys
     * @param {string} countData.notes - Optional notes
     * @returns {Promise<void>}
     */
    async saveCount(countData) {
      if (!countData.count_key) {
        throw new Error('count_key is required to complete a count');
      }
      try {
        await sendEvent({
          event_type: 'COUNT_COMPLETED',
          event_data: {
            count_key: countData.count_key,
            count_qt: countData.count_qt,
            count_serial_keys: countData.count_serial_keys || null,
            notes: countData.notes || null,
          }
        });
        Notify.create({
          message: $t('count_saved'),
          color: 'theme-green',
          position: 'top',
        });
      } catch (error) {
        console.error('Error saving count:', error);
        throw error;
      }
    },
    resetCounting() {
      this.sessionData = null;
      this.selectedPosition = null;
    }
  }
});
