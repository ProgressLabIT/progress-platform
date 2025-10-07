import { defineStore } from "pinia";
import { Notify } from "quasar";
import { api } from "@/boot/axios"
import { useNavStore } from 'app/src/stores/navigation';

const nav = useNavStore();

export const useListsStore = defineStore('lists', {
  state: () => ({
    headers: [],
    listMovements: [],
    selectedItem: undefined,
    tempQuantity: 0,
    tempSerials: [],
    productTraceabilityMap: {} // Acts as cache across multiple loadListMovements calls
  }),
  getters: {
    byDateAndPartner: (state) => {
      // First group by date, then by partner
      const dateMap = state.headers.reduce((result, list) => {
        const date = list.due_by;
        if (!result[date]) {
          result[date] = {};
        }

        const partnerCode = list.references.partner_code;
        if (!result[date][partnerCode]) {
          result[date][partnerCode] = [];
        }

        result[date][partnerCode].push(list);
        return result;
      }, {});

      // Sort lists within each partner by code
      Object.values(dateMap).forEach(partners => {
        Object.values(partners).forEach(lists => {
          lists.sort((a, b) => a.code.localeCompare(b.code));
        });
      });

      // Convert to array of [date, partnersMap] entries, sorted by date
      return Object.entries(dateMap)
        .sort(([dateA], [dateB]) => dateA.localeCompare(dateB))
        .map(([date, partners]) => {
          // Sort partners by partner_name
          const sortedPartners = Object.entries(partners)
            .sort(([, listsA], [, listsB]) =>
              listsA[0].references.partner_name.localeCompare(listsB[0].references.partner_name)
            );
          return [date, sortedPartners];
        });
    },
    listMovementsByItem: (state) => {
      // Group movements by item - all movements belong to a single list
      if (state.listMovements.length === 0) {
        return [];
      }

      // Get the list header for reference
      const listKey = state.listMovements[0].movement_list_key;
      const list = state.headers.find(l => l._key === listKey);
      if (!list) {
        return [];
      }

      const movementsByItem = Object.groupBy(state.listMovements, m => m.movement_list_item);
      return Object.entries(movementsByItem).map(([item, movements]) => {
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
    },
    getMovementByKey: (state) => {
      return (movementKey) => {
        return state.listMovements.find(m => m._key == movementKey)
      }
    },
    getMovementBySerial: (state) => {
      return ({ serialCode, productCode }) => {
        return state.listMovements.find(m => m.serial_code === serialCode && m.product_code === productCode)
      }
    },
    itemSerials: (state) => {
      return state.selectedItem?.movements
        ?.filter(m => (m.serial_key || m.serial_code) && m.qt_confirmed == 1 && m.status == 'planned')
        ?.sort((a, b) => a.serial_code.localeCompare(b.serial_code))
    },
    movementQuantity: (state) => {
      return state?.selectedItem?.type === 'serial'
      ? state.tempSerials.length
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
    async ensureProductTraceability(productKey) {
      // Check if product is already cached
      if (!(productKey in this.productTraceabilityMap)) {
        const { data: product } = await api.get(`/product/${productKey}`)
        this.productTraceabilityMap[productKey] = !!product.traceability_level
      }
    },
    async loadListMovements(listKey) {
      const { data } = await api.get(`/movement`, { params: { list_key: listKey, limit: 100000 } })
      const movement_data = data.filter(m => m.type != 'reversal' && !m.inverse_movement_key)

      const productKeys = [...new Set(movement_data.map(m => m.product_key))]

      // Ensure all product traceability data is loaded (in parallel)
      await Promise.all(productKeys.map(key => this.ensureProductTraceability(key)))

      this.listMovements = movement_data.map(m => ({
        ...m,
        use_serials: this.productTraceabilityMap[m.product_key]
      }))
    },
    update(movementUpdate) {
      const movement = this.listMovements.find(m => m._key == movementUpdate._key)
      movement.qt_confirmed = movementUpdate.qt_confirmed
    }
  }
})
