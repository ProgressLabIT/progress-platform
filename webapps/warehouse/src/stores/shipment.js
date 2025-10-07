import { defineStore } from "pinia";
import { api } from '@/boot/axios';
import { Loading, Notify } from 'quasar';
import { sendEventsBulk } from '@/composables/bulkEvent';
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
    },
    shipmentQuantity: (state) => {
      return state.selectedInventory.reduce((acc, i) => acc + i.selected, 0);
    }
  },
  actions: {
    loadInventory(params) {
      api.get(`/inventory`, { params: {
        product_key: this.product._key,
        ...params,
      } }).then((resp) => {
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
          position_from: inventoryItem.path.slice(-1)[0].position_key,
          serial_key: inventoryItem.serial_key,
          product_key: this.product._key,
          qt_planned: item.selected,
          qt_confirmed: item.selected,
        });
      }

      // Build events array with just event-specific data
      const events = movements.map(movement => ({
        event_type: 'MOVEMENT_COMPLETED',
        ...movement,
        position_to: 'OUT',
        status: 'completed',
        movement_type: 'shipment',
        start: now,
        end: now
      }));

      try {
        await sendEventsBulk(events, now);
        Notify.create({
          message: 'Movimenti registrati',
          position: 'top',
          color: 'theme-green',
          timeout: 1500,
        });
        return true;
      } catch (err) {
        // Error already shown by sendEventsBulk
        return false;
      }
    }
  }
})
