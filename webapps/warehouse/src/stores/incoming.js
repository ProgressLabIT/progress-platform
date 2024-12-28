import { defineStore } from "pinia";

export const useIncomingStore = defineStore('incoming', {
  state: () => ({
    product: undefined,
    serials: [],
    quantity: 0,
    positions: [],
    stage: 'product',
    recentProducts: [],
    recentPositions: [],
  }),
  getters: {
    refQuantity: (state) => state.product?.traceability_level ? state.serials.length : state.quantity
  }
})
