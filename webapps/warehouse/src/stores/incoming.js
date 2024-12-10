import { defineStore } from "pinia";

export const useIncomingStore = defineStore('incoming', {
  state: () => ({
    product: undefined,
    quantity: 0,
    positions: [],
    stage: 'product',
  }),
})
