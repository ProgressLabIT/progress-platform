<template>
  <q-page class="q-px-md q-py-md column fit q-gutter-y-sm">
    <div class="text-h1 q-mb-sm col-auto">
      Liste di spedizione
    </div>

    <q-scroll-area v-if="lists.headers.length" class="col">
      <template v-for="([date, partnerLists]) in lists.byDateAndPartner" :key="date">
        <!-- Date Header -->
        <div class="row items-center q-gutter-x-md q-mt-lg">
          <q-separator class="col" />
          <div class="col-auto text-h5 low-text weight-bold" :class="{ 'text-white': date <= today }">
            {{ date }}
          </div>
        </div>

        <!-- Customer Header -->
        <template v-for="([customer, customerLists]) in partnerLists" :key="customer">
          <div class="text-h4 full-width row justify-between items-baseline q-mt-md">
            <div class="col highlight">
              {{  customerLists[0].references.partner_name }} ({{ customerLists[0].references.partner_code }})
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
            :class="{ due: list.due_by === today, overdue: list.due_by < today }"
            @click="$router.push({ name: 'ShipmentList', params: { listKey: list._key }})">
            <div>
              {{ list.code  }}
            </div>
            <div>
              {{ getListCounts(list._key).completed }} / {{ getListCounts(list._key).total }}
            </div>
          </q-card>
        </template>
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
const today = new Date().toISOString().slice(0,10);

function getListCounts(listKey) {
  const listItems = lists.movementsByListAndItem[listKey]
  return {
    completed: listItems.filter(i => i.qt_confirmed === i.qt_planned).length,
    total: listItems.length
  }
}
</script>

<style scoped lang="sass">
.overdue
  font-weight: bold
  background-color: #e79110 !important

.due
  font-weight: bold
  background-color: var(--theme-blue) !important
</style>
