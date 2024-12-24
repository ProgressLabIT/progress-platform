<template>
  <div class="column col q-gutter-y-md">
    <!-- Display selected serials when in serial mode -->
    <div class="text-h6">
      {{ $t('contents') }}
      <q-chip size="sm" color="theme-grey" class="q-ml-sm">
        {{ transfer.contents.length }}
      </q-chip>
    </div>
    <div class="row q-col-gutter-x-xs q-mt-sm">
      <!-- Show first 3 serial numbers as chips -->
      <div v-for="item in transfer.contents.slice(0,3)" :key="item._key" class="col-auto">
        <q-chip color="theme-grey" class="text-body2" :icon="contentIcon[item.type]">
          <span>{{ item.code }}</span>
          <span v-if="item.type === 'product'">x{{ item.quantity }}</span>
        </q-chip>
      </div>
      <!-- Show count of remaining serials if more than 3 are selected -->
      <div v-if="transfer.contents.length > 3" class="col-auto">
        <q-chip color="theme-grey" class="text-body2">
          +{{ transfer.contents.length - 3 }}
        </q-chip>
      </div>
    </div>



    <!-- <div class="text-h6">{{ $t('destination') }}</div> -->
    <div class="text-h3 q-mt-lg">{{ $t(list.message) }}</div>
    <SearchOrScan v-model="filter" @update:model-value="searchPositions" />

    <div class="text-h6">POSIZIONI {{ list.type }}</div>
    <div class="col scroll">
      <div class="row full-width q-col-gutter-x-sm">
        <div v-for="pos in list.items" :key="pos._key" class="col-auto">
          <q-chip clickable outline class="text-body1" @click="setDestination(pos)">
            {{ pos.code }}
          </q-chip>
        </div>
      </div>
    </div>


    <q-space />
    <q-btn
      color="primary"
      :label="$t('position_create')"
      @click="showCreateContainerBottomSheet = true"
    />
    <q-btn
      color="primary"
      :label="$t('back')"
      @click="transfer.stage = 'start'"
    />

    <SlideUpCard
      v-model="showCreateContainerBottomSheet"
    >
      <CreateContainerForm
        :max="1"
        @hide="showCreateContainerBottomSheet=false"
        @select="(containers) => setDestination(containers[0])"
      />
    </SlideUpCard>
  </div>
</template>

<script setup>
import SearchOrScan from '@/components/SearchOrScan.vue';
import { ref, computed } from 'vue';
import { useTransferStore } from '@/stores/transfer';
import { api } from '@/boot/axios';
import SlideUpCard from '@/components/SlideUpCard.vue';
import CreateContainerForm from '@/components/CreateContainerForm.vue';
import { Notify } from 'quasar';


const transfer = useTransferStore();
const filter = ref('');
const results = ref([]);
const showCreateContainerBottomSheet = ref(false);
const list = computed(() => {

  if (results.value.length === 0) {
    if (filter.value.length > 0) {
      return { type: 'DISPONIBILI', items: [], message: 'no_results' };
    }
    else {
      return {
        type: 'RECENTI',
        items: transfer.recentPositions.filter(pos => pos._key !== transfer.startPosition._key),
        message: 'scan_destination_position'
      };
    }
  }
  return {
    type: 'DISPONIBILI',
    items: results.value.filter(pos => pos._key !== transfer.startPosition._key),
    message: 'scan_destination_position'
  };
});

const contentIcon = {
  product: 'mdi-apps',
  serial: 'mdi-cube-scan',
  position: 'mdi-package-variant-closed',
}

function searchPositions() {
  api
    .get('position', {
      params: { search: filter.value, }
    })
    .then((response) => {
      if (response.data.length === 0) {
        results.value = [];
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
}

function setDestination(pos) {
  transfer.destinationPosition = pos;
  transfer.stage = 'confirm';
}
</script>
