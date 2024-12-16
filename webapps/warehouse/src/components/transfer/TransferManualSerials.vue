<template>
  <div class="col column">

    <div class="col-auto q-mb-sm text-body2 item-center">
      {{ $t(message) }}
    </div>

    <SearchOrScan
      v-model="filter"
      @update:model-value="search"
    />

      <div
        v-if="transfer.selectedSerials.length"
        class="col-auto row items-center q-gutter-x-sm q-mb-sm text-h6">
        <div>{{ $t('selected') }}</div>
        <q-avatar size="xs" color="theme-grey">
          <div class="smaller highlight">{{ transfer.selectedSerials.length }}</div>
        </q-avatar>
      </div>

      <div class="col-auto scroll q-my-md column">
        <q-card
          v-for="item in transfer.selectedSerials"
          :key="item.key"
          v-ripple
          bordered
          flat
          class="bg-theme-blue q-px-md q-py-md q-mb-sm"
          @click="toggleItem(item)"
        >
          <div class="text-h6 text-low">{{ item.product.code }}</div>
          <div class="text-body1 highlight">{{ item.code }}</div>
        </q-card>
      </div>

      <div class="col-auto row items-center q-gutter-x-sm q-mb-sm text-h6">
        <div>{{ $t('results') }}</div>
        <q-avatar size="xs" color="theme-grey">
          <div class="smaller highlight">{{ serialList.length }}</div>
        </q-avatar>
      </div>

      <div class="col scroll q-my-md column">
        <q-card
          v-for="item in serialList"
          :key="item.key"
          v-ripple
          bordered
          flat
          class="surface2 q-px-md q-py-md q-mb-sm"
          @click="toggleItem(item)"
        >
          <div class="text-h6 text-low">{{ item.product.code }}</div>
          <div class="text-body1 highlight">{{ item.code }}</div>
        </q-card>
      </div>


    <q-space />

    <q-btn
      :disable="transfer.selectedSerials.length === 0"
      color="theme-blue"
      :label="$t('next')"
      class="col-auto full-width"
      @click="next"
    />

  </div>
</template>

<script setup>

import { Notify } from 'quasar';
import { ref, computed } from 'vue';
import SearchOrScan from '@/components/SearchOrScan.vue';
import { api } from 'app/src/boot/axios';
import { useTransferStore } from '@/stores/transfer';
import { useI18n } from 'vue-i18n';

const transfer = useTransferStore();
const filter = ref('');
const results = ref([]);
const message = ref('scan_serial')
const { t } = useI18n();


function search() {
  console.log(filter.value);
  if (!filter.value) {
    reset();
    return;
  }
  else {
    api.get('serial', { params: { serial_search: filter.value } })
    .then(response => {
      if (response.data.length === 0) {
        results.value = [];
        message.value = 'no_results';
      } else if (response.data.length === 1) {
        // if only one result, toggle it and notify the user
        const serial = response.data[0];
        const action = toggleItem(serial);
        Notify.create({
          message: action === 'added' ? t('serial_added') : t('serial_removed'),
          caption: serial.code,
          position: 'top',
          color: action === 'added' ? 'theme-green' : 'theme-orange',
          icon: action === 'added' ? 'mdi-check' : 'mdi-close',
          timeout: 1500,
        });
        filter.value = '';
        reset();
      } else {
        // show search results
        results.value = response.data;
      }
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
}

const serialList = computed(() => {
  return [
    ...results.value.filter(item => !transfer.selectedSerials.find(serial => serial._key === item._key))
  ];
});


function reset() {
  message.value = 'scan_serial';
  results.value = [];
  document.getElementById('search-input').focus();
}

function toggleItem(item) {
  const index = transfer.selectedSerials.findIndex(serial => serial._key === item._key);
  index !== -1 // if item is already in the list, remove it
    ? transfer.selectedSerials.splice(index, 1)
    : transfer.selectedSerials.push(item);

  return index === -1 ? 'added' : 'removed'
}

function next() {
  transfer.stage = 'destination';
}

</script>
