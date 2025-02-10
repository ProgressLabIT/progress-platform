import { defineStore } from "pinia";

export const useTransferStore = defineStore('transfer', {
  state: () => ({
    selectMode: undefined, // 'position' or 'serials'
    product: undefined,
    startPosition: undefined,
    contents: [],
    destinationPosition: undefined,
    stage: 'start',
    recentPositions: {
      from: [],
      to: [],
    },
  }),
})
