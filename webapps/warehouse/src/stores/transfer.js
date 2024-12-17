import { defineStore } from "pinia";

export const useTransferStore = defineStore('transfer', {
  state: () => ({
    selectMode: undefined, // 'position' or 'serials'
    startPosition: undefined,
    contents: [],
    destinationPosition: undefined,
    stage: 'start',
    recentPositions: [],
  }),
})
