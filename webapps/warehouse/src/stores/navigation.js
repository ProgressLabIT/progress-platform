import { defineStore } from "pinia";

export const useNavStore = defineStore('navigation', {
  state: () => ({
    dynamicBreadcrumb: [],
    loading: false
  }),
})
