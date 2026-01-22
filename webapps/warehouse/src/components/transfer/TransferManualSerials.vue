<template>
  <div class="col column q-gutter-y-sm">

    <div class="col-auto q-mb-sm text-body2 item-center">
      {{ $t(message) }}
    </div>

    <div class="row q-col-gutter-sm">
      <div class="col-6">
        <SearchOrScan
          v-model="serialCodeFilter"
          label="Seriale"
          @update:model-value="search"
        />
      </div>
      <div class="col-6">
        <q-input
          filled
          dense
          clearable
          input-class="text-uppercase"
          label="Prodotto"
          v-model="productCodeFilter"
          @update:model-value="search"
        >
          <template #append>
            <q-icon name="mdi-filter" />
          </template>
        </q-input>
      </div>
    </div>

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
          <div class="text-h6 text-low">{{ item.product_code }}</div>
          <div class="text-body1 highlight">{{ item.serial_code }}</div>
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
          <div class="text-h6 text-low">{{ item.product_code }}</div>
          <div class="text-body1 highlight">{{ item.serial_code }}</div>
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
const serialCodeFilter = ref('');
const productCodeFilter = ref('');
const results = ref([]);
const message = ref('scan_serial')
const { t } = useI18n();


function search() {
  api.get('inventory', { params: {
    serial_search: serialCodeFilter.value,
    product_search: productCodeFilter.value
  }})
  .then(response => {
    if (response.data.length === 0) {
      results.value = [];
      message.value = 'no_results';
    } else {
      // Map inventory results to match expected model
      if (response.data.length === 1 && response.data[0].serial_code === serialCodeFilter.value) {
        // if only one result, toggle it and notify the user
        const serial = response.data[0];
        const action = toggleItem(serial);
        Notify.create({
          message: action === 'added' ? t('serial_added') : t('serial_removed'),
          caption: serial.serial_code,
          position: 'top',
          color: action === 'added' ? 'theme-green' : 'theme-orange',
          icon: action === 'added' ? 'mdi-check' : 'mdi-close',
          timeout: 1500,
        });
        serialCodeFilter.value = '';
        reset();
      } else {
        // show search results
        results.value = response.data;
      }
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

const serialList = computed(() => {
  // Server-side filtering is handled by the API via product_search parameter
  // Only filter out already selected items (UI state)
  return results.value.filter(item => !transfer.contents.find(serial => serial._key === item._key));
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
    : transfer.contents.push({...item, type: 'serial', code: item.serial_code});

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
