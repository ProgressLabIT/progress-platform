import { defineStore } from "pinia";

export const useTransferStore = defineStore('transfer', {
  state: () => ({
    selectMode: undefined, // 'position' or 'serials'
    startPosition: undefined,
    product: undefined,
    quantity: undefined,
    selectedSerials: [],
    destinationPosition: undefined,
    stage: 'start',
    recentPositions: [],
  }),
})
