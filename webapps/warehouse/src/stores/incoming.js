import { defineStore } from "pinia";

export const useIncomingStore = defineStore('incoming', {
  state: () => ({
    product: undefined,
    quantity: 0,
    positions: [],
  }),
  getters: {
    positionKeys: (state) => state.positions.map(p => p._key)
  }
})
