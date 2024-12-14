<template>
  <q-page
    class="q-px-md q-py-lg column fit"
  >

    <template v-if="results.length === 0">
      <q-space />
      <div v-if="filter.length === 0" class="col-auto q-mb-sm text-h1 item-center" style="width: 70%;">
        {{  $t('scan_start_position_or_serial') }}
      </div>
      <div  v-else class="col-auto q-mb-sm text-h1 item-center" style="width: 70%;">
        {{  $t('no_results') }}
      </div>
    </template>

    <template v-else>

      <!-- PRODUCT LIST -->
      <div class="col-auto q-mb-sm text-h6">
        {{ $t(list_label) }} ({{ results.length }})
      </div>


      <div class="col scroll q-my-md column">
        <q-card
          v-for="item in results"
          :key="item.key"
          v-ripple
          bordered
          flat
          class="surface2 q-px-md q-py-md q-mb-sm"
          @click="selectItem(item)"
        >
          <div v-if="startFrom === 'serial'">
            <div class="text-h6 text-low">{{ item.product.code }}</div>
            <div class="text-body1 highlight">{{ item.code }}</div>
          </div>

          <div v-else>
            <div class="text-body1 highlight">{{ item.code }}</div>
          </div>
        </q-card>
      </div>

    </template>

    <q-space />

     <!-- PRODUCT SEARCH -->
    <SearchOrScan
      v-model="filter"
      @update:model-value="search"
    />

    <q-btn-toggle
      v-model="startFrom"
      @update:model-value="reset"
      spread
      unelevated
      toggle-color="theme-blue"
      color="blue-backdrop"
      :options="[
        { label: $t('position'), value: 'position' },
        { label: $t('serial'), value: 'serial' },
      ]"
    />
  </q-page>
</template>

<script setup>
import { ref } from 'vue';
import SearchOrScan from '@/components/SearchOrScan.vue';
import { api } from 'app/src/boot/axios';
import { Notify } from 'quasar';


const startFrom = ref('position');
const filter = ref('');
const results = ref([]);
const list_label = ref('recent')

function loadResults(endpoint, params = {}) {
  api.get(endpoint, { params })
    .then(response => {
      results.value = response.data;
      list_label.value = 'results'
    })
    .catch(error => {
      Notify.create({
        message: error.response.data.message,
        position: 'top',
        color: 'red',
        icon: 'error',
      });
    });
}


function reset() {
  filter.value = '';
  results.value = [];
  document.getElementById('search-input').focus();
}

function selectItem(item) {
  console.log(item);
}

function search() {
  if (filter.value === '') {
    results.value = [];
    return;
  }
  if (startFrom.value === 'serial') {
    loadResults('serial', { serial_search: filter.value });
  } else {
    loadResults('position', { search: filter.value });
  }
}
</script>
