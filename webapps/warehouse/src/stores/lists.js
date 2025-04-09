import { defineStore } from "pinia";
import { Notify } from "quasar";
import { api } from "@/boot/axios"
import { useNavStore } from 'app/src/stores/navigation';

const nav = useNavStore();

export const useListsStore = defineStore('lists', {
  state: () => ({
    headers: [],
    movements: [],
    selectedItem: undefined,
    tempQuantity: 0,
    productTraceabilityMap: {}
  }),
  getters: {
    byPartner: (state) => {
      const map = state.headers.reduce((result, list) => {
        (result[list.references.partner_code] = result[list.references.partner_code] || []).push(list);
        return result;
      }, {})
      return Object.entries(map)
    },
    movementsByListAndItem: (state) => {
      return state.headers.reduce((result, list) => {
        const listMovementsByItem = Object.groupBy(state.movements.filter(m => m.movement_list_key == list._key), m => m.movement_list_item)
        const listItems = Object.entries(listMovementsByItem).map(([item, movements]) => {
          const qt_planned = movements.reduce((sum, mov) => sum += mov.qt_planned, 0)
          const qt_confirmed = movements.reduce((sum, mov) => sum += mov.qt_confirmed, 0)
          const type = movements[0].use_serials ? 'serial' : 'quantity'

          const plannedMovements = movements.filter(m => m.status == 'planned')
          const serialsProvided = plannedMovements.length > 0 && plannedMovements.every(m => m.serial_code !== null)

          return {
            item,
            product_code: movements[0].product_code,
            product_description: movements[0].product_description,
            product_key: movements[0].product_key,
            references: movements[0].references,
            listKey: movements[0].movement_list_key,
            reference: list.type == 'receipt' ? movements[0].references.purchase_doc : movements[0].references.sales_doc,
            type,
            serialsProvided,
            qt_planned,
            qt_confirmed,
            movements
          };
        })
        result[list._key] = listItems
        return result
      }, {})
    },
    getMovementByKey: (state) => {
      return (movementKey) => {
        return state.movements.find(m => m._key == movementKey)
      }
    },
    getMovementBySerial: (state) => {
      return ({ serialCode, productCode }) => {
        return state.movements.find(m => m.serial_code === serialCode && m.product_code === productCode)
      }
    },
    itemSerials: (state) => {
      return state.selectedItem?.movements
        ?.filter(m => (m.serial_key || m.serial_code) && m.qt_confirmed == 1 && m.status == 'planned')
        ?.sort((a, b) => a.serial_code.localeCompare(b.serial_code))
    },
    movementQuantity: (state) => {
      return state?.selectedItem?.type === 'serial'
      ? state.selectedItem.movements.reduce((sum, m) => sum += m.qt_confirmed, 0)
      : state.tempQuantity
    }
  },
  actions: {
    async loadLists(type) {
      this.$reset();
      nav.loading = true;
      try {
        // fetch lists
        this.headers = (await api.get('/movement-list', { params: { type, open_only: true }})).data

        if (this.headers.length) {
          // fetch movements and group them by list and product
          const params = new URLSearchParams()
          this.headers.forEach(l => params.append('list_key', l._key))
          const movement_data = (await api.get('/movement', { params })).data
          const productKeys = [...new Set(movement_data.map(m => m.product_key))]
          const traceabilityPromises = productKeys.map(async productKey => {
            const { data: product } = await api.get(`/product/${productKey}`)
            return [productKey, !!product.traceability_level]
          })
          this.productTraceabilityMap = Object.fromEntries(await Promise.all(traceabilityPromises))
          this.movements = movement_data.map(m => ({
            ...m,
            use_serials: this.productTraceabilityMap[m.product_key]
          }))
        }
        nav.loading = false;
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
    },
    update(movementUpdate) {
      const movement = this.movements.find(m => m._key == movementUpdate._key)
      movement.qt_confirmed = movementUpdate.qt_confirmed
    }
  }
})
