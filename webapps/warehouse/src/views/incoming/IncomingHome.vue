<template>
  <q-page class="q-px-md q-py-md column fit q-gutter-y-sm">
    <div class="text-h1 q-mb-sm col-auto">
      {{ $t('incoming_lists_title') }}
    </div>

    <q-scroll-area v-if="lists.headers.length" class="col">
      <template v-for="([date, partnerLists]) in lists.byDateAndPartner" :key="date">
        <!-- Date Header -->
        <div class="row items-center q-gutter-x-md q-mt-xl">
          <q-separator class="col" />
          <div class="col-auto text-h5 low-text weight-bold" :class="{ 'text-white': date <= today }">
            {{ date }}
          </div>
        </div>

        <!-- Supplier Lists -->
        <template v-for="([supplier, supplierLists]) in partnerLists" :key="supplier">
          <div class="text-h4 full-width row justify-between items-baseline q-mt-md">
            <div class="col">
              <span class="highlight">
                {{ supplierLists[0].references.partner_name }}
              </span>
              <span class="text-body2 q-ml-sm smaller text-low">
                {{ supplierLists[0].references.partner_code }}
              </span>
            </div>
            <div class="col-auto smaller text-low">
              Righe controllate / totali
            </div>
          </div>

          <!-- Supplier Lists -->
          <q-card
            v-for="list in supplierLists"
            :key="list._key"
            v-ripple
            class="row text-body1 surface1 justify-between q-pa-md q-mt-xs"
            :class="{ due: list.due_by === today, overdue: list.due_by < today }"
            @click="$router.push({ name: 'IncomingList', params: { listKey: list._key }})">
            <div>
              {{ list.code  }}
            </div>
            <div>
              {{ list.counts.completed }} / {{ list.counts.completed + list.counts.planned }}
            </div>
          </q-card>
        </template>
      </template>
    </q-scroll-area>

    <div v-else class="col">
      {{ $t('incoming_no_lists') }}
    </div>

    <q-btn
      color="theme-blue"
      :label="$t('incoming_new')"
      @click="$router.push({ name: 'IncomingManual' })"
    />
  </q-page>
</template>

<script setup>
import { useListsStore } from 'stores/lists'
const lists = useListsStore();
const today = new Date().toISOString().slice(0,10);
</script>

<style scoped lang="sass">
.overdue
  font-weight: bold
  background-color: #e79110 !important

.due
  font-weight: bold
  background-color: var(--theme-blue) !important
</style>
