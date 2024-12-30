<template>
  <q-page class="q-px-md q-py-lg column fit">
    <div class="text-h1 q-mb-lg">
      Liste di carico
    </div>

    <template v-if="loading">
      LOADING
    </template>

    <template v-else-if="lists.headers.length">
      <template v-for="([supplier, supplierLists]) in lists.byPartner" :key="supplier">
        <!-- Supplier Header -->
        <div class="text-h3 full-width row justify-between items-baseline q-mt-lg q-mb-sm">
          <div class="col highlight">
            {{  supplierLists[0].references.partner_name }}
          </div>
          <div class="col-auto smaller text-disabled">
            Righe controllate / totali
          </div>
        </div>

        <!-- Supplier Lists -->
          <q-card
            v-for="list in supplierLists"
            :key="list._key"
            v-ripple
            class="row text-body1 surface1 justify-between q-pa-md"
            @click="null">
            <div>
              {{ list.code  }}
            </div>
            <div side>
              {{ getListCounts(list._key).completed }} / {{ getListCounts(list._key).total }}
            </div>
          </q-card>
      </template>
    </template>

    <template v-else>
      NO DATA
    </template>

    <q-space></q-space>
    <q-btn
      color="theme-blue"
      label="NUOVO RICEVIMENTO"
      @click="$router.push({ name: 'IncomingManual' })"
    />
  </q-page>
</template>

<script setup>
import { ref } from 'vue';
import { useListsStore } from 'stores/lists'

const lists = useListsStore();

const loading = ref(true);

lists.loadData().then(() => setTimeout(() => loading.value = false, 500));

function getListCounts(listKey) {
  return {
    completed: lists.movements[listKey].filter(m => m.status == 'completed').length,
    total: lists.movements[listKey].length
  }
}
</script>
