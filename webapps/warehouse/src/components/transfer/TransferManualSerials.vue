<template>
  <div class="col column q-gutter-y-sm">

    <div class="col-auto q-mb-sm text-body2 item-center">
      {{ $t(message) }}
    </div>

    <SearchOrScan
      v-model="filter"
      @update:model-value="search"
    />

    <q-scroll-area class="col">

      <div
        v-if="transfer.contents.length"
        class="col-auto row items-center q-gutter-x-sm q-mb-sm text-h6">
        <div>{{ $t('selected') }}</div>
        <q-chip size="xs" color="theme-grey">
          <div class="smaller highlight">{{ transfer.contents.length }}</div>
        </q-chip>
      </div>

      <div class="col-auto scroll q-my-md column">
        <q-card
          v-for="item in transfer.contents"
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
        <q-chip size="xs" color="theme-grey">
          <div class="smaller highlight">{{ serialList.length }}</div>
        </q-chip>
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


  </q-scroll-area>

    <q-btn
      :disable="transfer.contents.length === 0"
      color="theme-blue"
      :label="$t('next')"
      class="col-auto full-width"
      @click="next"
    />
    <q-btn
      color="grey"
      :label="$t('cancel')"
      class="col-auto full-width"
      @click="cancel"
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
import { useRouter } from 'vue-router';

const router = useRouter();
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
    ...results.value.filter(item => !transfer.contents.find(serial => serial._key === item._key))
  ];
});


function reset() {
  message.value = 'scan_serial';
  results.value = [];
  document.getElementById('search-input').focus();
}

function toggleItem(item) {
  const index = transfer.contents.findIndex(serial => serial._key === item._key);
  index !== -1 // if item is already in the list, remove it
    ? transfer.contents.splice(index, 1)
    : transfer.contents.push({...item, type: 'serial'});

  return index === -1 ? 'added' : 'removed'
}

function next() {
  transfer.stage = 'destination';
}

function cancel() {
  transfer.$reset();
  router.push({ name: 'TransferRoot' });
}

</script>
