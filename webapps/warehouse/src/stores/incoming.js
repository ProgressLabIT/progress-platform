import { defineStore } from "pinia";

export const useIncomingStore = defineStore('incoming', {
  state: () => ({
    product: undefined,
    quantity: 0,
    positions: undefined,
    position_keys: undefined,
  }),
})
