import { defineStore } from "pinia";
import { api } from '@/boot/axios';
import { Loading, Notify } from 'quasar';
import { sendEvent } from '@/composables/event';
import { timestamp } from '@/lib/TimeHandling';

export const useShipmentStore = defineStore('shipment', {
  state: () => ({
    recentProducts: [],
    product: undefined,
    inventory: [],
    selectedInventory: [],
    stage: 'product',
  }),
  getters: {
    inventorySelectedQt: (state) => {
      return (inventoryKey) => {
        const match = state.selectedInventory.find(i => i._key === inventoryKey);
        return match ? match.selected : 0;
      }
    }
  },
  actions: {
    loadInventory(positionSearch, serialSearch) {
      Loading.show();
      api.get(`/inventory`, { params: {
        product_key: this.product._key,
        position_search: positionSearch,
        serial_search: serialSearch,
      }}).then((resp) => {
        this.inventory = resp.data;
        Loading.hide();
      });
    },

    async confirmShipment() {
      const now = timestamp();
      const movements = [];

      for (const item of this.selectedInventory) {
        const inventoryItem = this.inventory.find(i => i._key === item._key);
        movements.push({
          position_from: `Position/${inventoryItem.path.slice(-1)[0].position_key}`,
          serial_key: inventoryItem.serial_key,
          product_key: this.product._key,
          qt_planned: item.selected,
          qt_confirmed: item.selected,
        });
      }

      // Process non-serial items
      const nonSerialItems = this.selectedInventory.filter(item => {
        const inventoryItem = this.inventory.find(i => i._key === item._key);
        return !inventoryItem?.serial_key && item.selected > 0;
      });

      for (const item of nonSerialItems) {
        const inventoryItem = this.inventory.find(i => i._key === item._key);
        movements.push({
          position_from: `Position/${inventoryItem.path.slice(-1)[0].position_key}`,
          product_key: this.product._key,
          qt_planned: item.selected,
          qt_confirmed: item.selected,
        });
      }

      // Send movement events one by one
      for (const movement of movements) {
        try {
          await sendEvent({
            event_type: 'ADD_MOVEMENT',
            event_data: {
              movement: {
                ...movement,
                position_to: 'Position/OUT',
                status: 'completed',
                type: 'shipment',
                start: now,
                end: now
              }
            },
          });
          Notify.create({
            message: 'Movimento registrato',
            position: 'top',
            color: 'theme-green',
            timeout: 1500,
          });
        } catch (err) {
          Notify.create({
            position: 'top',
            timeout: 0,
            message: err,
            color: 'theme-orange',
            actions: [
              { label: 'Close', textColor: 'white', handler: () => undefined }
            ]
          });
          return false;
        }
      }
      return true;
    }
  }
})
