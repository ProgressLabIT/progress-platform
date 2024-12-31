import { defineStore } from "pinia";
import { Notify } from "quasar";
import { api } from "@/boot/axios"

export const useListsStore = defineStore('lists', {
  state: () => ({
    headers: [],
    movements: [],
  }),
  getters: {
    byPartner: (state) => {
      const map = state.headers.reduce((result, list) => {
        (result[list.references.partner_code] = result[list.references.partner_code] || []).push(list);
        return result;
      }, {})
      return Object.entries(map)
    },
    movementsByListAndProduct: (state) => {
      const result = {}
      state.headers.forEach(list => {
        const listMovements = state.movements.filter(m => m.movement_list_key === list._key).map(m => {
          const refKey = Object.values(m.references).filter(r => r).join('-')
          const itemKey = `${m.product_code}-${refKey}`
          return { ...m, itemKey }
        })
        const itemKeys = new Set(listMovements.map(m => m.itemKey))
        const listItems = []
        itemKeys.forEach(ik => {
          const itemMovements = listMovements.filter(m => m.itemKey === ik)
          const qt_planned = itemMovements.reduce((sum, mov) => sum += mov.qt_planned, 0)
          const qt_confirmed = itemMovements.reduce((sum, mov) => sum += mov.qt_confirmed, 0)
          const type = 'quantity' //itemMovements[0].serial_code ? 'serial' : 'quantity'
          listItems.push({
            itemKey: ik,
            product_code: itemMovements[0].product_code,
            product_description: itemMovements[0].product_description,
            references: itemMovements[0].references,
            type,
            qt_planned,
            qt_confirmed,
            movements: itemMovements
          });
        })
        result[list._key] = listItems
      })
      return result
    }
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
