import { defineStore } from "pinia";
import { Notify } from "quasar";
import { api } from "@/boot/axios"

export const useListsStore = defineStore('lists', {
  state: () => ({
    headers: [],
    movements: [],
    movementsByListAndProduct: {} // by list key & product
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
          // fetch movements and group them by list and product
          const listKeys = new URLSearchParams()
          this.headers.forEach(l => listKeys.append('list_key', l._key))
          this.movements = (await api.get('/movement', { params: listKeys })).data
          this.headers.forEach(list => {
            const listMovements = this.movements.filter(m => m.movement_list_key === list._key)
            const product_codes = new Set(listMovements.map(m => m.product_code))
            const listItems = []
            product_codes.forEach(p => {
              const productMovements = listMovements.filter(m => m.product_code === p)
              const qt_planned = productMovements.reduce((sum, mov) => sum += mov.qt_planned, 0)
              const qt_confirmed = productMovements.reduce((sum, mov) => sum += mov.qt_confirmed, 0)
              const type = productMovements[0].serial_code ? 'serial' : 'quantity'
              listItems.push({ product_code: p, type, qt_planned, qt_confirmed, movements: productMovements });
            })
            this.movementsByListAndProduct[list._key] = listItems
          })
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
