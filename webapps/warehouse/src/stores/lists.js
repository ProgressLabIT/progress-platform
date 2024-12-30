import { defineStore } from "pinia";
import { Notify } from "quasar";
import { api } from "@/boot/axios"

export const useListsStore = defineStore('lists', {
  state: () => ({
    headers: [],
    movements: {} // by list key
  }),
  getters: {
    byPartner: (state) => {
      const map = state.headers.reduce((result, list) => {
        (result[list.references.partner_code] = result[list.references.partner_code] || []).push(list);
        return result;
      }, {})
      return Object.entries(map)
    },
  },
  actions: {
    async loadData() {
      try {
        // fetch lists
        this.headers = (await api.get('/movement-list', { params: { type: 'receipt', open_only: true }})).data

        if (this.headers.length) {
          // fetch movements and group them by list key
          const listKeys = new URLSearchParams()
          this.headers.forEach(l => listKeys.append('list_key', l._key))

          const movementData = (await api.get('/movement', { params: listKeys })).data
          this.movements = movementData.reduce((result, movement) => {
            (result[movement.movement_list_key] = result[movement.movement_list_key] || []).push(movement)
            return result
          }, {})
        }
      }
      catch (err) {
        console.log(err)
        Notify.create({
          position: 'top',
          message: err,
          timeout: 0,
          color: 'theme-red',
          actions: [
            { label: 'Close', textColor: 'white', handler: () => undefined }
          ]
        })
      }
    }
  }
})
