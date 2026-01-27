<template>
  <div class="col column q-pb-md">

    <!-- ================================ -->
    <!-- POSITION SELECTION -->
    <!-- ================================ -->
    <template v-if="countingStore.selectedPosition === null">
      <div class="text-h3 q-mb-md">{{ $t('start_from_position') }}</div>
      <SearchOrScan v-model="filter" @update:model-value="searchPositions" />

      <!-- NO RESULTS -->
      <template v-if="positionResults.length === 0">
        <div class="text-h2">{{ $t('no_results') }}</div>
      </template>

      <!-- AVAILABLE POSITIONS -->
      <template v-else>
        <div class="q-mt-lg text-h6">POSIZIONI {{ positionResultsType }}</div>
        <div class="col scroll q-my-md">
          <div class="row q-col-gutter-sm">
            <div v-for="pos in positionResults" :key="pos._key" class="col-auto">
              <q-card flat clickable bordered class="q-pa-sm transparent" @click="selectPosition(pos._key)">
                {{ pos.code }}
              </q-card>
            </div>
          </div>
        </div>
      </template>

      <q-space></q-space>

      <!-- ACTIONS -->
      <q-btn
        color="primary"
        outline
        :label="$t('select_root_position')"
        @click="selectPosition('IN')"
      />
    </template>


    <!-- ================================ -->
    <!-- POSITION CONTENTS -->
    <!-- ================================ -->

    <template v-if="countingStore.selectedPosition !== null">
      <div class="row items-center q-mb-sm">
        <div class="text-h3 q-mr-sm">{{ $t('position') }}</div>
        <q-chip
          outline
          class="text-body2"
        >
          <span v-if="countingStore.selectedPosition.path.length > 0">
            {{ getPathString(countingStore.selectedPosition) }}
          </span>
          <q-icon name="mdi-warehouse" v-else />
        </q-chip>
        <q-space />
        <q-btn
          size="sm"
          dense
          flat
          color="theme-grey"
          :label="$t('reset')"
          label-left
          icon-right="mdi-close-circle"
          @click="resetPositionNavigation"
        />
      </div>

      <CountingContentsView
        ref="contentsRef"
        :session-data="sessionData"
        :contents="positionContents"
        :count-records="countRecords"
        :position-status="positionStatus"
        :position-key="countingStore.selectedPosition?._key"
        :loading="loading"
        @position-selected="selectPosition"
        @refresh-position="refreshCurrentPosition"
      />

      <!-- ================================ -->
      <!-- ACTIONS -->
      <!-- ================================ -->
      <q-space></q-space>
      <q-btn
        color="theme-blue"
        outline
        :label="$t('add_count_for_product')"
        class="full-width q-mb-sm"
        @click="showProductSearch = true"
      />
      <q-btn
        v-if="positionContents.length === 0"
        color="theme-blue"
        :label="$t('confirm_empty_position')"
        class="full-width q-mb-sm"
        @click="showEmptyPositionConfirmation = true"
      />
      <q-btn
        color="theme-grey"
        :label="$t('back')"
        class="full-width"
        @click="goUpOneLevel()"
      />
    </template>


    <!-- ================================ -->
    <!-- Product Search Card -->
    <!-- ================================ -->
    <CountingProductSearchCard
      v-model="showProductSearch"
      :position-contents="positionContents"
      :selected-position="countingStore.selectedPosition"
      @product-selected="handleProductSelected"
    />

    <!-- ================================ -->
    <!-- Empty Position Confirmation Card -->
    <!-- ================================ -->
    <CountingEmptyPositionCard
      v-model="showEmptyPositionConfirmation"
      :session-key="sessionData._key"
      :position-key="countingStore.selectedPosition?._key"
      @confirmed="handleEmptyPositionConfirmed"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { api } from '@/boot/axios';
import { store } from '@/boot/store';
import { useCountingStore } from '@/stores/counting';
import SearchOrScan from '@/components/SearchOrScan.vue';
import CountingProductSearchCard from './CountingProductSearchCard.vue';
import CountingEmptyPositionCard from './CountingEmptyPositionCard.vue';
import CountingContentsView from './CountingContentsView.vue';
import { Loading } from 'quasar';

const props = defineProps({
  sessionData: {
    type: Object,
    required: true
  }
});

const { t: $t } = useI18n();

const countingStore = useCountingStore();

const loading = ref(false);
const filter = ref('');
const positionResults = ref([]);
const positionResultsType = ref('RECENTI');
const positionContents = ref([]);
const positionStatus = ref({});
const showProductSearch = ref(false);
const countRecords = ref([]);
const showEmptyPositionConfirmation = ref(false);
const contentsRef = ref(null);

const positionPath = computed(() => countingStore.selectedPosition?.path || []);

function getPathString(position) {
  return position?.path?.map(p => p.position_code).join(' > ') || '';
}

// --- Helpers for filtered contents ---

function aggregateInventoryItems(filteredItems) {
  // Process all inventory items in a single reduce, creating uniform data model
  const processedItems = filteredItems.reduce((acc, item) => {
    if (item.type === 'serial') {
      // Serial items: aggregate by product_key
      const key = item.product_key;
      if (!acc.serialsByProduct[key]) {
        acc.serialsByProduct[key] = {
          _key: `aggregated_${item.product_key}`,
          type: 'serial',
          code: item.product_code,
          product_description: item.product_description,
          product_key: item.product_key,
          quantity: 0,
          serial_keys: [],
          inventory_keys: [],
          counting: false,
          count_by: null,
          count_user: null,
          counting_items: [] // Track individual counting status
        };
      }
      acc.serialsByProduct[key].quantity += 1;
      acc.serialsByProduct[key].serial_keys.push(item.serial_key);
      acc.serialsByProduct[key].inventory_keys.push(item._key);
      // Track counting status for aggregated serials (track all items)
      acc.serialsByProduct[key].counting_items.push({
        counting: item.counting || false,
        count_by: item.count_by || null,
        count_user: item.count_user || null
      });
    } else {
      // Product/Position items: convert _key to array
      acc.items.push({
        ...item,
        inventory_keys: [item._key]
      });
    }
    return acc;
  }, { items: [], serialsByProduct: {} });

  // Process aggregated serials to determine if they're all locked by the same user
  Object.keys(processedItems.serialsByProduct).forEach(key => {
    const aggregated = processedItems.serialsByProduct[key];
    // Check if ALL serials are locked and by the same user
    const allLocked = aggregated.counting_items.every(item => item.counting === true);
    if (allLocked && aggregated.counting_items.length > 0) {
      // Check if all are locked by the same user
      const uniqueCountBy = new Set(aggregated.counting_items.map(i => i.count_by).filter(Boolean));
      if (uniqueCountBy.size === 1) {
        // All locked by the same user
        aggregated.counting = true;
        aggregated.count_by = aggregated.counting_items[0].count_by;
        aggregated.count_user = aggregated.counting_items[0].count_user;
      }
      // If multiple users, don't show as locked
    }
    // Clean up temporary tracking field
    delete aggregated.counting_items;
  });

  return processedItems;
}

function buildCountOnlyItems() {
  // Product keys that already have inventory in this position
  const inventoryProductKeys = new Set(
    positionContents.value
      .map(item => item.product_key)
      .filter(Boolean)
  );

  const countOnlyMap = new Map();
  const selectedPosKey = countingStore.selectedPosition?._key || null;

  countRecords.value.forEach(record => {
    const productKey = record.product_key;
    if (!productKey || inventoryProductKeys.has(productKey)) {
      // Skip products that already have inventory in this position
      return;
    }

    // Ensure record belongs to currently selected position
    const recordPositionKeyRaw = record.position_key || (record._to ? record._to : null);
    const recordPositionKey = recordPositionKeyRaw && recordPositionKeyRaw.includes('/')
      ? recordPositionKeyRaw.split('/').pop()
      : recordPositionKeyRaw;

    if (selectedPosKey && recordPositionKey && recordPositionKey !== selectedPosKey) {
      return;
    }

    const code = record.product_code || '';
    const description = record.product_description || '';

    const aggregateKey = `${productKey}_${recordPositionKey || ''}`;
    if (!countOnlyMap.has(aggregateKey)) {
      const isSerialProduct = !!record.product_traceability_level;

      countOnlyMap.set(aggregateKey, {
        _key: `count_only_${aggregateKey}`,
        type: isSerialProduct ? 'serial' : 'product',
        code,
        product_code: code,
        product_description: description,
        product_key: productKey,
        position_key: recordPositionKey || selectedPosKey,
        position_code: countingStore.selectedPosition?.code || null,
        quantity: null,          // No system quantity for virtual items
        inventory_keys: [],      // No inventory backing
        isCountOnly: true,       // Flag for outline-only rendering
        traceability_level: record.product_traceability_level || null,
      });
    }
  });

  return Array.from(countOnlyMap.values());
}

function loadLatestUsedPositions() {
  Loading.show();
  api.get('movement/latest-positions', { params: {
    position_type: 'from',
    movement_type: 'transfer',
    limit: 10
  }})
  .then((resp) => {
    positionResults.value = resp.data;
    Loading.hide();
    positionResultsType.value = 'RECENTI';
  });
}

function searchPositions() {
  Loading.show();
  let params = {};

  if (!filter.value || filter.value.length === 0) {
    loadLatestUsedPositions();
    positionResultsType.value = 'RECENTI';
  } else {
    params.search = filter.value;
    params.limit = 100;

    api.get('position', { params }).then((resp) => {
      if (resp.data.length === 1 && resp.data[0].code === filter.value) {
        selectPosition(resp.data[0]._key);
      } else {
        positionResults.value = [...resp.data];
      }
      Loading.hide();
      positionResultsType.value = 'DISPONIBILI';
    });
  }
}

async function loadPositionContents(positionKey) {
  Loading.show();
  try {
    const response = await api.get(`/position/${positionKey}`);

    // Handle new response structure: { position, path, contents }
    if (response.data && response.data.position) {
      // Attach path to position object so it's available via computed property
      const positionWithPath = {
        ...response.data.position,
        path: response.data.path || []
      };
      countingStore.selectedPosition = positionWithPath;
      positionContents.value = response.data.contents || [];
    } else {
      // Fallback for old response format (array of contents)
      positionContents.value = Array.isArray(response.data) ? response.data : [];
    }

    // Fetch position completion status for this position and session
    await loadPositionCompletionStatus(positionKey);

    // Fetch count records for this position and session
    await loadCountRecords(positionKey);
  } finally {
    Loading.hide();
  }
}

async function loadPositionCompletionStatus(positionKey) {
  if (!props.sessionData?._key || !positionKey) {
    return;
  }

  try {
    const response = await api.get('/inventory/count-position-status', {
      params: {
        session_key: props.sessionData._key,
        parent_key: positionKey
      }
    });
    positionStatus.value = response.data;
  } catch (error) {
    console.error('Error loading position completion status:', error);
    positionStatus.value = {};
  }
}

async function loadCountRecords(positionKey) {
  if (!props.sessionData?._key) {
    return;
  }

  try {
    // The API expects full document IDs (e.g., "Position/KEY") for position_key
    const response = await api.get('/inventory/count-record', {
      params: {
        count_session_key: props.sessionData._key,
        position_key: positionKey,
        limit: 1000
      }
    });
    countRecords.value = response.data || [];
  } catch (error) {
    console.error('Error loading count records:', error);
    countRecords.value = [];
  }
}

async function selectPosition(positionKey) {
  Loading.show();
  try {
    filter.value = '';
    await loadPositionContents(positionKey);
  } finally {
    Loading.hide();
  }
}

function goUpOneLevel() {
  filter.value = '';
  // Get parent position from path (second-to-last element)
  if (positionPath.value.length > 1) {
    const parentPosition = positionPath.value[positionPath.value.length - 2];
    selectPosition(parentPosition.position_key);
  } else {
    // At root position, reset to position selection
    countingStore.selectedPosition = null;
    positionContents.value = [];
  }
}

function resetPositionNavigation() {
  filter.value = '';
  countingStore.selectedPosition = null;
  positionContents.value = [];
}
onMounted(() => {
  loadLatestUsedPositions();
});

function handleProductSelected(product) {
  if (!countingStore.selectedPosition?._key) {
    return;
  }
  contentsRef.value?.openForProduct(
    product,
    countingStore.selectedPosition._key,
    countingStore.selectedPosition.code
  );
}

function handleEmptyPositionConfirmed() {
  // Refresh position contents after empty position confirmation
  if (countingStore.selectedPosition?._key) {
    loadPositionContents(countingStore.selectedPosition._key);
  }
}

function refreshCurrentPosition() {
  if (countingStore.selectedPosition?._key) {
    loadPositionContents(countingStore.selectedPosition._key);
  }
}
</script>

<style lang="sass" scoped>
.grid-style-transition
  transition: transform .28s, background-color .28s

</style>
