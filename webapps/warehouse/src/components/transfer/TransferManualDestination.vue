<template>
  <div class="column col q-gutter-y-md">
    <!-- Display selected serials when in serial mode -->
    <div v-if="transfer.selectMode === 'serials'">
      <div class="text-h6">
        {{ $t('serial', 2) }}
        <q-avatar size="sm" color="theme-grey" class="q-ml-sm">
          {{ transfer.selectedSerials.length }}
        </q-avatar>
      </div>
      <div class="row q-col-gutter-x-xs q-mt-sm">
        <!-- Show first 3 serial numbers as chips -->
        <div v-for="serial in transfer.selectedSerials.slice(0,3)" :key="serial" class="col-auto">
          <q-chip color="theme-grey" class="text-body2 highlight">
            {{ serial.code }}
          </q-chip>
        </div>
        <!-- Show count of remaining serials if more than 3 are selected -->
        <div v-if="transfer.selectedSerials.length > 3" class="col-auto">
          <q-chip color="theme-grey" class="text-body2">
            +{{ transfer.selectedSerials.length - 3 }}
          </q-chip>
        </div>
      </div>
    </div>

    <!-- Display position details when in position mode -->
    <div v-else-if="transfer.selectMode === 'position'" class="q-mb-md">
      <div class="row q-col-gutter-x-sm">
        TEST
      </div>
    </div>

    <div class="text-h6">{{ $t('destination') }}</div>
    <SearchOrScan v-model="filter" @update:model-value="searchPositions" />
    <div class="text-body2">{{ $t(message) }}</div>

    <div class="col scroll">
      <div class="row full-width q-col-gutter-x-sm q-mt-md">
        <div v-for="pos in results" :key="pos._key" class="col-auto">
          <q-chip clickable outline class="text-body1" @click="setDestination(pos)">
            {{ pos.code }}
          </q-chip>
        </div>
      </div>
    </div>


    <q-space />
    <q-btn
      color="primary"
      :label="$t('back')"
      @click="transfer.stage = 'start'"
    />
  </div>
</template>

<script setup>
import SearchOrScan from '@/components/SearchOrScan.vue';
import { ref } from 'vue';
import { useTransferStore } from '@/stores/transfer';
import { api } from '@/boot/axios';
import { Notify } from 'quasar';


const transfer = useTransferStore();
const filter = ref('');
const message = ref('scan_destination_position');
const results = ref([]);

function searchPositions() {
  api
    .get('position', {
      params: { search: filter.value, }
    })
    .then((response) => {
      if (response.data.length === 0) {
        results.value = [];
        message.value = 'no_results';
      } else if (response.data.length === 1) {
        // if only one result, toggle it and notify the user
        setDestination(response.data[0]);
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

function reset() {
  filter.value = '';
  results.value = [];
  message.value = 'scan_destination_position';
}

function setDestination(pos) {
  transfer.destinationPosition = pos;
  transfer.stage = 'confirm';
}
</script>
