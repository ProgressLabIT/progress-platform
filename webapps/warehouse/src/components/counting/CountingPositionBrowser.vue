<template>
  <div class="col column full-width q-pb-md">

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

      <SearchOrScan
        v-model="filter"
        class="q-mb-md"
      />

      <div class="text-h6" v-if="!loading && positionContents.length === 0">{{ $t('no_contents') }}</div>


      <!-- ================================ -->
      <!-- ITEM LIST -->
      <!-- ================================ -->
      <template v-else>
        <div class="row items-center justify-between q-mb-md">
          <div class="text-h6">{{ $t('contents') }}</div>
          <q-checkbox
            v-model="hideCountedFilter"
            left-label
            dense
            :label="$t('hide_counted')"
            :disable="loading"
            class="text-body2"

          />
        </div>
        <q-virtual-scroll
          :items="filteredContents"
          v-slot="{ item }"
          class="col q-mb-md thin-scrollbar"
        >
          <q-item
            :key="item._key"
            clickable
            class="content-card q-my-xs q-pa-md text-body1"
            style="height: 75px; max-width: 95vw"
            :style="{ 'border-color': getCountInfo(item).hasStarted ? 'var(--theme-blue)' : null }"
            :class="[getColor(item), {'locked-item': getCountInfo(item).hasStarted && getCountInfo(item).startedBy === store.state.session.user._key}]"
            @click="selectItem(item)"
          >

            <!-- ICON -->
            <q-item-section side class="col-auto">
              <q-icon :name="contentIcon[item.type]" />
            </q-item-section>

            <!-- CODE AND DESCRIPTION -->
            <q-item-section>
              <div class="row items-center highlight">
                <div class="col-auto q-mr-sm">{{ item.code }}</div>
                <!-- Added Icon -->
                <div class="col-auto column items-center">
                <q-icon
                    v-if="item.isCountOnly"
                    name="mdi-plus-circle"
                    color="theme-orange"
                    size="16px"
                />
                </div>
                <!-- Resume/Active Icon -->
                <div class="col-auto column items-center">
                  <q-icon
                      v-if="getCountInfo(item).hasStarted"
                      :name="getCountInfo(item).startedBy === store.state.session.user._key ? 'mdi-progress-pencil' : 'mdi-lock'"
                      :color="getCountInfo(item).startedBy === store.state.session.user._key ? 'theme-blue' : 'theme-orange'"
                      size="16px"
                  />
                </div>
                <!-- Completed Icon -->
                <div class="col-auto column items-center">
                  <q-icon
                      v-if="getCountInfo(item).completedCount > 0 && !(getCountInfo(item).hasStarted && getCountInfo(item).startedBy === store.state.session.user._key)"
                      name="mdi-check-circle"
                      color="theme-green"
                      size="16px"
                  />
                </div>
              </div>
              <q-item-label v-if="item.product_description" caption class="ellipsis">
                {{ item.product_description }}
              </q-item-label>
            </q-item-section>

            <!-- QUANTITY -->
            <q-item-section v-if="item.quantity && !blindQuantities" side class="col-auto">
              <div class="text-body2">
                {{ item.quantity }}
                <span v-if="getCountedQuantity(item) !== null" class="text-low q-ml-xs">
                  / {{ getCountedQuantity(item) }}
                </span>
              </div>
            </q-item-section>

            <!-- COUNTED QUANTITY (blind mode) -->
            <q-item-section v-if="blindQuantities && getCountedQuantity(item) !== null" side class="col-auto">
              <div class="text-body2 text-low">
                {{ getCountedQuantity(item) }}
              </div>
            </q-item-section>

            <!-- POSITION FULLY CHECKED -->
            <q-item-section
              v-if="item?.type === 'position' && item?.position_key && item.position_key in positionStatus"
              side
              class="col-auto"
            >
              <div class="row items-baseline">
                <q-icon name="mdi-check-circle" :size="positionStatus[item.position_key] === 'empty' ? '10px' : '25px'"/>
                <q-icon v-if="positionStatus[item.position_key] === 'empty'" name="mdi-package-variant-remove" size="27px"/>
              </div>
            </q-item-section>

            <!-- COUNT NUMBER & USER -->
            <q-item-section
              v-if="getCountInfo(item).hasRecords && (getCountInfo(item).startedBy || getCountInfo(item).completedBy.length > 0)"
              side
              class="col-auto"
            >
              <q-icon
                v-if="getCountInfo(item).completedBy.length > 1"
                name="mdi-account-group"
                size="20px"
                color="theme-grey"
              />
              <BaseUserAvatar
                v-else
                :user="usersByKeys[getCountInfo(item).startedBy || getCountInfo(item).completedBy[0]]"
                :show_name="false"
                size="20px"
                dense
              />
            </q-item-section>
          </q-item>
        </q-virtual-scroll>
      </template>

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
    <!-- Counting Cards -->
    <!-- ================================ -->
    <CountingQuantityCard
      v-if="selectedItem && selectedItem.serial_key === null"
      :item="selectedItem"
      @close="unselectItem()"
    />

    <CountingSerialsCard
      v-if="selectedItem && selectedItem?.serial_key !== null"
      :item="selectedItem"
      :blind-mode="blindSerials"
      @close="unselectItem()"
    />


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
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { api } from '@/boot/axios';
import { store } from '@/boot/store';
import { useCountingStore } from '@/stores/counting';
import SearchOrScan from '@/components/SearchOrScan.vue';
import CountingQuantityCard from './CountingQuantityCard.vue';
import CountingSerialsCard from './CountingSerialsCard.vue';
import CountingProductSearchCard from './CountingProductSearchCard.vue';
import CountingEmptyPositionCard from './CountingEmptyPositionCard.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
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
const selectedItem = ref(null);
const showProductSearch = ref(false);
const usersByKeys = ref({});
const countRecords = ref([]);
const hideCountedFilter = ref(false);
const showEmptyPositionConfirmation = ref(false);

api.get('user').then((resp) => {
  usersByKeys.value = resp.data.detail.reduce((acc, user) => {
    acc[user._key] = user;
    return acc;
  }, {});
});

const blindQuantities = computed(() => props.sessionData.blind_quantities ?? true);
const blindSerials = computed(() => props.sessionData.blind_serials ?? true);

const positionPath = computed(() => countingStore.selectedPosition?.path || []);

const contentIcon = {
  product: 'mdi-apps',
  serial: 'mdi-cube-scan',
  position: 'mdi-package-variant-closed',
};

function getColor(item) {
  if (item && item.isCountOnly) {
    // Count-only items are rendered as outline-only, without background color
    return `bg-grey-backdrop`;
  }
  const colorMap = {
    product: 'blue',
    serial: 'green',
    position: 'red'
  };
  const color = colorMap[item.type];
  return `bg-${color}-backdrop`;
}

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
    const recordPositionKey = record.position_key || (record._to ? record._to.split('/').pop() : null);
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
        selectPosition(resp.data[0]);
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
  if (!props.sessionData?._key || !positionKey) return;

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
  if (!props.sessionData?._key) return;

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

// Helper: Group count records by product_key + position_key
function groupRecordsByProductAndPosition(records, positionKey) {
  return records.reduce((acc, record) => {
    const recordProductKey = record.product_key || (record._from ? record._from.split('/').pop() : null);
    const recordPositionKey = record.position_key || (record._to ? record._to.split('/').pop() : null);

    if (recordProductKey && recordPositionKey === positionKey) {
      const key = `${recordProductKey}_${recordPositionKey}`;
      if (!acc.has(key)) {
        acc.set(key, []);
      }
      acc.get(key).push(record);
    }
    return acc;
  }, new Map());
}

// Helper: Build count info for a single item
function buildCountInfoForItem(item, records) {
  const completedRecords = records.filter(r => r.status === 'completed' || r.status === 'submitted' || r.status === 'confirmed');
  const startedRecords = records.filter(r => r.status === 'started');

  return {
    hasRecords: records.length > 0,
    completedCount: completedRecords.length,
    startedCount: startedRecords.length,
    hasStarted: startedRecords.length > 0,
    startedBy: startedRecords.length > 0 ? startedRecords[0].user_key : null,
    completedBy: [...new Set(completedRecords.map(r => r.user_key).filter(Boolean))],
    allRecords: records
  };
}

// Helper: Build count info map from items and grouped records
function buildCountInfoMap(items, recordsByKey, positionKey) {
  return items.reduce((map, item) => {
    if (!item.product_key) return map;

    const key = `${item.product_key}_${positionKey}`;
    const records = recordsByKey.get(key) || [];
    map.set(item._key, buildCountInfoForItem(item, records));

    return map;
  }, new Map());
}

// Pre-compute count info map for all items to avoid repeated filtering
const countInfoMap = computed(() => {
  const positionKey = countingStore.selectedPosition?._key;

  if (!positionKey || !countRecords.value.length) {
    return new Map();
  }

  // Pre-process count records by product_key + position_key for faster lookup
  const recordsByKey = groupRecordsByProductAndPosition(countRecords.value, positionKey);

  // Get all items that could appear in filteredContents (before text filtering)
  const processedInventory = aggregateInventoryItems(positionContents.value);
  const countOnlyItems = buildCountOnlyItems();
  const allItems = [
    ...processedInventory.items,
    ...Object.values(processedInventory.serialsByProduct),
    ...countOnlyItems
  ];

  // Build count info for each item
  return buildCountInfoMap(allItems, recordsByKey, positionKey);
});

const filteredContents = computed(() => {
  const searchLower = (filter.value || '').toLowerCase();

  // 1) Inventory-based items - aggregate serials by product
  const processedInventory = aggregateInventoryItems(positionContents.value);

  // 2) Count-only virtual items (counts without inventory)
  const countOnlyItems = buildCountOnlyItems(''); // Pass empty string since we filter below

  // 3) Combine everything
  const allItems = [
    ...processedInventory.items,
    ...Object.values(processedInventory.serialsByProduct),
    ...countOnlyItems
  ];

  // 4) Apply text filter to all items
  const textFiltered = searchLower
    ? allItems.filter(item => {
        const code = (item.code || '').toLowerCase();
        const description = (item.product_description || '').toLowerCase();
        const searchContext = code + ' ' + description;
        return searchContext.includes(searchLower);
      })
    : allItems;

  // 5) Filter out completed counts if hideCountedFilter is active
  const filteredItems = hideCountedFilter.value
    ? textFiltered.filter(item => {
        // Filter out items with completed counts
        const countInfo = countInfoMap.value.get(item._key);
        if (countInfo && countInfo.completedCount > 0) {
          return false;
        }
        // Filter out positions that are counted or empty
        if (item.type === 'position' && item.position_key && item.position_key in positionStatus.value) {
          return false;
        }
        return true;
      })
    : textFiltered;

  // 6) Sort by code attribute
  const sortedItems = filteredItems.sort((a, b) => a.code.localeCompare(b.code));
  return sortedItems;
});


// Auto-select item if exactly one matches the filter
watch(filteredContents, async (filtered) => {
  if (filter.value && filtered.length === 1) {
    // Check if filter matches the item's code exactly (case-insensitive)
    const itemCode = filtered[0].code?.toLowerCase() || '';
    if (itemCode === filter.value.toLowerCase()) {
      await nextTick();
      selectItem(filtered[0]);
      filter.value = '';
    }
  }
});

onMounted(() => {
  loadLatestUsedPositions();
});

function selectItem(item) {
  // Check if item is locked by another user using count records
  const countInfo = countInfoMap.value.get(item._key);
  if (countInfo?.hasStarted && countInfo.startedBy) {
    const currentUserKey = store.state.session.user._key;
    if (countInfo.startedBy !== currentUserKey) {
      // Item is locked by another user, block access
      Notify.create({
        message: $t('count_locked_by_other_user'),
        color: 'theme-orange',
        position: 'top',
        timeout: 3000
      });
      return;
    }
    // Item is locked by current user, proceed normally
  }

  // Use countInfo to determine if count is active (more reliable than item.counting from API)
  const isCounting = countInfo?.hasStarted || false;
  const countBy = countInfo?.startedBy || item.count_by || null;

  // Get the last count record for pre-filling
  const lastCountRecord = getLastCountRecord(item);

  if (item.type === 'position') {
    selectPosition(item.position_key);
  } else if (item.isAggregatedSerial) {
    // For aggregated serials, pass the aggregated item with serials array
    selectedItem.value = {
      _key: item._key,
      product_key: item.product_key,
      product_code: item.product_code,
      product_description: item.product_description,
      position_key: countingStore.selectedPosition._key,
      position_code: countingStore.selectedPosition.code,
      serial_key: 'aggregated', // Mark as aggregated
      serials: item.serials,     // Pass all serials for this product
      quantity: item.quantity,
      counting: isCounting,
      count_by: countBy,
      inventory_keys: item.inventory_keys || [],
      path: [{ position_key: countingStore.selectedPosition._key, position_code: countingStore.selectedPosition.code }],
      lastCountRecord,
    };
  } else {
    // Convert position API response format to inventory format for counting cards
    selectedItem.value = {
      _key: item._key,
      product_key: item.product_key,
      product_code: item.code,
      product_description: item.product_description,
      position_key: countingStore.selectedPosition._key,
      position_code: countingStore.selectedPosition.code,
      serial_key: item.type === 'serial' ? item.serial_key : null,
      serial_code: item.type === 'serial' ? item.code : null,
      quantity: item.quantity || 0,
      counting: isCounting,
      count_by: countBy,
      inventory_keys: item.inventory_keys || [item._key],
      path: [{ position_key: countingStore.selectedPosition._key, position_code: countingStore.selectedPosition.code }],
      lastCountRecord,
    };
  }
}

function unselectItem() {
  console.log('unselectItem');
  selectedItem.value = null;
  loadPositionContents(countingStore.selectedPosition._key);
}

// Helper function to get count info for display (uses pre-computed map)
function getCountInfo(item) {
  return countInfoMap.value.get(item._key) || {
    hasRecords: false,
    completedCount: 0,
    startedCount: 0,
    hasStarted: false,
    startedBy: null,
    completedBy: [],
    allRecords: []
  };
}

// Helper function to get counted quantity from count records
function getCountedQuantity(item) {
  const lastRecord = getLastCountRecord(item);
  return lastRecord?.counted_qt ?? null;
}

// Helper function to get the last completed count record for the current user
function getLastCountRecord(item) {
  const countInfo = getCountInfo(item);
  if (!countInfo.hasRecords || countInfo.allRecords.length === 0) {
    return null;
  }

  const currentUserKey = store.state.session.user._key;

  // Get completed/submitted/confirmed records by current user
  const completedRecords = countInfo.allRecords.filter(
    r => (r.status === 'completed' || r.status === 'submitted' || r.status === 'confirmed')
      && r.user_key === currentUserKey
  );

  if (completedRecords.length === 0) return null;

  // Sort by counted_at descending and return the most recent
  return completedRecords.sort((a, b) => {
    const dateA = a.counted_at ? new Date(a.counted_at) : new Date(0);
    const dateB = b.counted_at ? new Date(b.counted_at) : new Date(0);
    return dateB - dateA;
  })[0];
}

function handleProductSelected(product) {
  // Determine card type based on traceability_level
  const isSerialProduct = !!product.traceability_level;

  // Create item object for counting cards
  selectedItem.value = {
    _key: null, // No inventory key yet
    product_key: product._key,
    product_code: product.code,
    product_description: product.description,
    position_key: countingStore.selectedPosition._key,
    position_code: countingStore.selectedPosition.code,
    serial_key: isSerialProduct ? 'aggregated' : null,
    quantity: 0,
    counting: false,
    count_by: null,
    inventory_keys: [], // Empty - item doesn't exist in inventory yet
    path: [{ position_key: countingStore.selectedPosition._key, position_code: countingStore.selectedPosition.code }]
  };
}

function handleEmptyPositionConfirmed() {
  // Refresh position contents after empty position confirmation
  if (countingStore.selectedPosition?._key) {
    loadPositionContents(countingStore.selectedPosition._key);
  }
}
</script>

<style lang="sass" scoped>
.content-card
  border-radius: 5px
  border: 1px solid transparent

  // Ensure main content section labels always stack vertically
  :deep(.q-item__section--main)
    display: flex
    flex-direction: column
    min-width: 0

    .q-item__label
      display: block
      width: 100%

.locked-item
  border: 2px solid var(--theme-blue) !important

.grid-style-transition
  transition: transform .28s, background-color .28s

.thin-scrollbar
  // Firefox
  scrollbar-width: thin
  scrollbar-color: rgba(255, 255, 255, 0.3) transparent

  // WebKit browsers (Chrome, Safari, Edge)
  &::-webkit-scrollbar
    width: 6px

  &::-webkit-scrollbar-track
    background: transparent

  &::-webkit-scrollbar-thumb
    background: rgba(255, 255, 255, 0.3)
    border-radius: 3px

  &::-webkit-scrollbar-thumb:hover
    background: rgba(255, 255, 255, 0.5)
</style>

