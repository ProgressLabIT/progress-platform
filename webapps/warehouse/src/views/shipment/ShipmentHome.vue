<template>
  <q-page class="q-px-md q-py-md column fit q-gutter-y-sm">
    <div class="text-h1 q-mb-sm col-auto">
      Liste di spedizione
    </div>

    <q-scroll-area v-if="lists.headers.length" class="col">
      <template v-for="([customer, customerLists]) in lists.byPartner" :key="customer">
        <!-- Customer Header -->
        <div class="text-h4 full-width row justify-between items-baseline q-mt-lg">
          <div class="col highlight">
            {{  customerLists[0].references.partner_name }}
          </div>
          <div class="col-auto smaller text-disabled">
            Righe controllate / totali
          </div>
        </div>

        <!-- Customer Lists -->
          <q-card
            v-for="list in customerLists"
            :key="list._key"
            v-ripple
            class="row text-body1 surface1 justify-between q-pa-md q-mt-xs"
            @click="$router.push({ name: 'ShipmentList', params: { listKey: list._key }})">
            <div>
              {{ list.code  }}
            </div>
            <div>
              {{ getListCounts(list._key).completed }} / {{ getListCounts(list._key).total }}
            </div>
          </q-card>
      </template>
    </q-scroll-area>

    <div v-else class="col">
      Nessuna lista di spedizione disponibile
    </div>

    <q-btn
      color="theme-blue"
      label="NUOVA SPEDIZIONE"
      @click="$router.push({ name: 'ShipmentManual' })"
    />
  </q-page>
</template>

<script setup>
import { useListsStore } from '@/stores/lists'
const lists = useListsStore();

function getListCounts(listKey) {
  const listItems = lists.movementsByListAndItem[listKey]
  return {
    completed: listItems.filter(i => i.qt_confirmed === i.qt_planned).length,
    total: listItems.length
  }
}
</script>
