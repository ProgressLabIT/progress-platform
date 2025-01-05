<template>
  <div class="col column full-width">

    <div class="text-h3 q-mb-md">{{ $t('start_from_position') }}</div>

    <!-- POSITION SEARCH -->
    <SearchOrScan v-model="filter" @update:model-value="searchPositions" />

    <!-- NO RESULTS -->
    <template v-if="positionResults.length === 0">
      <div class="text-h2">{{ $t('no_results') }}</div>
    </template>

    <!-- AVAILABLE POSITIONS -->
    <template v-else>
      <div class="q-mt-lg text-h6">POSIZIONI {{ positionResultsType }}</div>
      <div class="col scroll">
        <div class="row full-width q-col-gutter-x-sm q-mt-md">
          <div v-for="pos in positionResults" :key="pos._key" class="col-auto">
            <q-chip clickable outline class="text-body1" @click="selectPosition(pos)">
              {{ pos.code }}
            </q-chip>
          </div>
        </div>
      </div>
    </template>

    <q-space></q-space>


    <q-btn
      color="primary"
      :label="$t('select_root_position')"
      @click="selectRootPosition()"
    />
    <div class="q-my-sm"></div>
    <q-btn
      color="theme-grey"
      :label="$t('cancel')"
      class="full-width"
      @click="router.push({ name: 'TransferRoot'})"
    />
    <div class="q-mx-xs"></div>


    <SlideUpCard
      :model-value="showContentTypeSelection !== null"
      @hide="showContentTypeSelection = null"
    >
      <TransferManualPositionAction
        :position="showContentTypeSelection"
        @select-container="selectContainer"
        @select-contents="selectContents(showContentTypeSelection)"
      />
    </SlideUpCard>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';
import SearchOrScan from '@/components/SearchOrScan.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';
import TransferManualPositionAction from '@/components/transfer/TransferManualPositionAction.vue';
import { useTransferStore } from '@/stores/transfer';
import { useRouter } from 'vue-router';

const router = useRouter();
const { t: $t } = useI18n();
const transfer = useTransferStore();

const loading = ref(false);

const filter = ref('');
const last_research = ref('');
const positionResults = ref([]);
const positionResultsType = ref('RECENTI');
const showContentTypeSelection = ref(null);




function searchPositions() {
  if (filter.value !== last_research.value) {
    if (filter.value === '') {
      loadLatestUsedPositions();
      positionResultsType.value = 'RECENTI'
    } else {
      loadPositions();
      positionResultsType.value = 'DISPONIBILI'
    }
  }
}


function loadLatestUsedPositions() {
  if (transfer?.recentPositions?.length) {
    positionResults.value = transfer?.recentPositions;
  }
  else {
    loading.value = true;
    api.get('movement/latest-positions', { params: {
      position_type: 'from',
      movement_type: 'transfer',
      limit: 10
    }})
    .then((resp) => {
      transfer.recentPositions = resp.data;
      positionResults.value = transfer?.recentPositions;
      loading.value = false;
      positionResultsType.value = 'RECENTI';
    });
  }
}

function loadPositions() {
  loading.value = true;
  let params = {};

  if (filter.value === last_research.value) {
    return
  }

  if (filter.value.length === 0) {
    loadLatestUsedPositions();
    positionResultsType.value = 'RECENTI'
  }

  else {
    params.search = filter.value;
    last_research.value = filter.value;
    params.limit = 100;

    api.get('position', { params }).then((resp) => {
      if (resp.data.length === 1) {
        selectPosition(resp.data[0]);
      }
      else {
        positionResults.value = [...resp.data];
      }
      loading.value = false;
      positionResultsType.value = 'DISPONIBILI';
    });
  }
}

function selectPosition(position) {
  // If position is a container, open dialog to select whole container or contents
  if (position.fixed == true) {
    selectContents(position);
    return
  }
  else {
    showContentTypeSelection.value = position;
  }
}

function selectRootPosition() {
  selectContents({
    fixed: true,
    _key: 'IN',
    code: 'IN',
  });
}

function selectContents(position) {
  transfer.startPosition = position;
  transfer.contents = [];
  transfer.stage = 'contents';
}


function selectContainer() {
  transfer.contents.push({
    type: 'position',
    ...showContentTypeSelection.value
  });
  transfer.stage = 'destination';
}

onMounted(() => {
  loadLatestUsedPositions();
});
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
