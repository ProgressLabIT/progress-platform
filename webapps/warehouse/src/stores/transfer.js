import { defineStore } from "pinia";

export const useTransferStore = defineStore('transfer', {
  state: () => ({
    selectMode: undefined, // 'position' or 'serials'
    startPosition: undefined,
    contents: {
      position: undefined,  // Full container to transfer
      serials: [],
      products: [], // {product_key: product, quantity: quantity}
    },
    destinationPosition: undefined,
    stage: 'start',
    recentPositions: [],
  }),
})
