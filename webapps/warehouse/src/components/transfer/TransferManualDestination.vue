<template>
  <div class="column col q-gutter-y-sm">
    <!-- Display selected serials when in serial mode -->
    <div class="text-h6">
      {{ $t('contents') }}
      <q-chip size="sm" color="theme-grey" class="q-ml-sm">
        {{ transfer.contents.length }}
      </q-chip>
    </div>
    <div class="row q-gutter-x-xs q-mt-sm">
      <!-- Show first 3 serial numbers as chips -->
      <ContentChip
        v-for="item in transfer.contents.slice(0,3)"
        :key="item._key"
        :item="item"
        :show-from-position="transfer.selectMode === 'product'"
      />
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

    <div class="text-h6 q-mt-md">POSIZIONI {{ list.type }}</div>
    <div class="col scroll">
      <div class="row q-col-gutter-sm">
        <div v-for="pos in list.items" :key="pos._key" class="col-auto">
          <q-card bordered class="text-body2 q-pa-sm transparent" @click="setDestination(pos)">
            {{ pos.code }}
          </q-card>
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
      color="theme-grey"
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
import ContentChip from '@/components/ContentChip.vue';


const transfer = useTransferStore();
const filter = ref('');
const results = ref([]);
const showCreateContainerBottomSheet = ref(false);


api.get('movement/latest-positions', { params: {
  position_type: 'to',
  movement_type: 'transfer',
  limit: 5
}})
.then((resp) => {
  transfer.recentPositions.to = resp.data;
});

const list = computed(() => {

  if (results.value.length === 0) {
    if (filter.value.length > 0) {
      return { type: 'DISPONIBILI', items: [], message: 'no_results' };
    }
    else {
      return {
        type: 'RECENTI',
        items: transfer.recentPositions.to.filter(pos => !startPositionKeys.value.includes(pos._key)),
        message: 'scan_destination_position'
      };
    }
  }
  return {
    type: 'DISPONIBILI',
    items: results.value,
    message: 'scan_destination_position'
  };
});

function getStartPositionKey(item) {
  return item.type === 'position' ? item.position_key : (transfer.startPosition?._key ?? item.path.slice(-1)[0].position_key);
}

const startPositionKeys = computed(() => {
  return [...new Set(transfer.contents.map(getStartPositionKey)), transfer.startPosition?._key];
});

function searchPositions() {
  api
    .get('position', {
      params: { search: filter.value, }
    })
    .then((response) => {
      const resultSet = response.data.filter(pos => !startPositionKeys.value.includes(pos._key));
      if (resultSet.length === 0) {
        results.value = [];
      } else if (resultSet.length === 1 && resultSet[0].code === filter.value) {
        // if only one result, toggle it and notify the user
        setDestination(resultSet[0]);
        reset();
      } else {
        // show search results
        results.value = resultSet;
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
  document.getElementById('search-input').focus()
}

function setDestination(pos) {
  transfer.destinationPosition = pos;
  transfer.stage = 'confirm';
}
</script>
