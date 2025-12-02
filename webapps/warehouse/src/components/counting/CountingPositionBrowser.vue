<template>
  <div class="col column full-width q-pb-md">
    <!-- POSITION SELECTION -->
    <template v-if="stage === 'position'">
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
              <q-card flat clickable bordered class="q-pa-sm transparent" @click="selectPosition(pos)">
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
        @click="selectRootPosition()"
      />
    </template>

    <!-- CONTENTS -->
    <template v-if="stage === 'contents'">
      <div class="row items-center q-mb-sm q-gutter-x-md">
        <div class="text-h3">{{ $t('position') }}</div>
        <q-chip class="highlight text-body2" color="theme-grey">{{ selectedPosition.code }}</q-chip>
      </div>

      <SearchOrScan
        v-model="filter"
        @update:model-value="loadPositionContents(selectedPosition._key)"
        class="q-mb-md"
      />

      <div class="text-h6" v-if="positionContents.length === 0">{{ $t('no_contents') }}</div>

      <template v-else>
        <div class="text-h6 q-mb-md">{{ $t('contents') }}</div>
        <q-scroll-area class="col q-mb-md">
          <q-list>
            <q-item
              v-for="item in filteredContents"
              :key="item._key"
              clickable
              class="content-card q-my-xs q-pa-md text-body1"
              :style="{ 'border-color': getCountInfo(item).hasStarted ? 'var(--theme-blue)' : null }"
              :class="[getColor(item), {'locked-item': getCountInfo(item).hasStarted && getCountInfo(item).startedBy === store.state.session.user._key              }]"
              @click="selectItem(item)"
            >
              <q-item-section side>
                <q-icon :name="contentIcon[item.type]" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="highlight">{{ item.code }}</q-item-label>
                <q-item-label caption>{{ item.product_description }}</q-item-label>
              </q-item-section>
              <q-item-section v-if="item.quantity && !blindMode" side>
                <div class="text-body2">
                  {{ item.quantity }}
                </div>
              </q-item-section>
              <q-item-section v-if="item.isCountOnly" side>
                <q-badge color="theme-orange" class="uppercase highlight q-pa-sm">
                  {{ $t('added') }}
                </q-badge>
              </q-item-section>
              <q-item-section v-if="getCountInfo(item).completedCount > 0" side>
                <div class="row items-center q-gutter-xs">
                  <span v-if="getCountInfo(item).completedCount > 1" class="text-body2">
                    {{ getCountInfo(item).completedCount }}x
                  </span>
                  <q-icon name="mdi-check-circle" color="theme-green" size="20px" />
                </div>
              </q-item-section>
              <q-item-section v-if="getCountInfo(item).hasStarted" side>
                <q-badge :color="getCountInfo(item).startedBy === store.state.session.user._key ? 'theme-blue' : 'theme-orange'" class="q-pa-sm uppercase highlight">
                  {{ getCountInfo(item).startedBy === store.state.session.user._key ? $t('count_resume') : $t('count_active') }}
                </q-badge>
              </q-item-section>
              <q-item-section v-if="getCountInfo(item).hasRecords && (getCountInfo(item).startedBy || getCountInfo(item).completedBy.length > 0)" side>
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
          </q-list>
        </q-scroll-area>
      </template>

      <q-space></q-space>
      <q-btn
        color="theme-blue"
        outline
        :label="$t('add_count_for_product')"
        class="full-width q-mb-sm"
        @click="showProductSearch = true"
      />
      <q-btn
        color="theme-grey"
        :label="$t('back')"
        class="full-width"
        @click="backToPositionSelection()"
      />
    </template>

    <!-- Counting Cards -->
    <CountingQuantityCard
      v-if="selectedItem && selectedItem.serial_key === null"
      :item="selectedItem"
      @close="unselectItem()"
    />

    <CountingSerialsCard
      v-if="selectedItem && selectedItem?.serial_key !== null"
      :item="selectedItem"
      @close="unselectItem()"
    />

    <!-- Product Search Card -->
    <SlideUpCard
      :model-value="showProductSearch"
      @hide="showProductSearch = false"
      height="90vh"
    >
      <div class="col column">
        <div class="col-auto q-mb-sm text-h3">
          {{ $t('product') }}
        </div>

        <!-- PRODUCT SEARCH -->
        <SearchOrScan v-model="productFilter" @update:model-value="searchProducts" />

        <!-- PRODUCT LIST -->
        <div class="col-auto q-mt-md q-mb-sm text-h6">
          {{ productListLabel }} ({{ productRows?.length || 0 }})
        </div>

        <q-scroll-area class="col">
          <q-list>
            <q-item
              v-for="product in productRows"
              :key="product._key"
              clickable
              dense
              class="content-card q-my-xs q-py-sm"
              :class="getProductColor(product)"
              @click="selectProductForCount(product)"
            >
              <q-item-section side>
                <q-icon :name="product.traceability_level ? 'mdi-cube-scan' : 'mdi-apps'" />
              </q-item-section>
              <q-item-section>
                <q-item-label class="highlight">{{ product.code }}</q-item-label>
                <q-item-label caption class="">{{ product.description }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-scroll-area>
      </div>
    </SlideUpCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { api } from '@/boot/axios';
import { store } from '@/boot/store';
import SearchOrScan from '@/components/SearchOrScan.vue';
import CountingQuantityCard from './CountingQuantityCard.vue';
import CountingSerialsCard from './CountingSerialsCard.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';

const props = defineProps({
  sessionData: {
    type: Object,
    required: true
  }
});

const { t: $t } = useI18n();

const loading = ref(false);
const stage = ref('position');
const filter = ref('');
const last_research = ref('');
const positionResults = ref([]);
const positionResultsType = ref('RECENTI');
const selectedPosition = ref(null);
const positionContents = ref([]);
const selectedItem = ref(null);
const showProductSearch = ref(false);
const productFilter = ref('');
const productListLabel = ref('Recenti');
const productRows = ref([]);
const productLastResearch = ref(undefined);
const usersByKeys = ref({});
const countRecords = ref([]);

api.get('user').then((resp) => {
  usersByKeys.value = resp.data.detail.reduce((acc, user) => {
    acc[user._key] = user;
    return acc;
  }, {});
});

const blindMode = computed(() => props.sessionData.blind_mode);

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

function getProductColor(product) {
  return product.traceability_level ? 'bg-green-backdrop' : 'bg-blue-backdrop';
}

// --- Helpers for filtered contents ---

function filterInventoryContents(search) {
  const searchLower = (search || '').toLowerCase();
  return positionContents.value.filter(item => {
    const searchContext = ((item.code || '') + ' ' + (item.product_code || '')).toLowerCase();
    return searchContext.includes(searchLower);
  });
}

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

function buildCountOnlyItems(search) {
  const searchLower = (search || '').toLowerCase();

  // Product keys that already have inventory in this position
  const inventoryProductKeys = new Set(
    positionContents.value
      .map(item => item.product_key)
      .filter(Boolean)
  );

  const countOnlyMap = new Map();
  const selectedPosKey = selectedPosition.value?._key || null;

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
    const searchContext = (code + ' ' + description).toLowerCase();

    // Apply same text filter
    if (searchLower && !searchContext.includes(searchLower)) {
      return;
    }

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
        position_code: selectedPosition.value?.code || null,
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
  loading.value = true;
  api.get('movement/latest-positions', { params: {
    position_type: 'from',
    movement_type: 'transfer',
    limit: 10
  }})
  .then((resp) => {
    positionResults.value = resp.data;
    loading.value = false;
    positionResultsType.value = 'RECENTI';
  });
}

function searchPositions() {
  loading.value = true;
  let params = {};

  if (filter.value === last_research.value) {
    return;
  }

  if (!filter.value || filter.value.length === 0) {
    loadLatestUsedPositions();
    positionResultsType.value = 'RECENTI';
  } else {
    params.search = filter.value;
    last_research.value = filter.value;
    params.limit = 100;

    api.get('position', { params }).then((resp) => {
      if (resp.data.length === 1 && resp.data[0].code === filter.value) {
        selectPosition(resp.data[0]);
      } else {
        positionResults.value = [...resp.data];
      }
      loading.value = false;
      positionResultsType.value = 'DISPONIBILI';
    });
  }
}

async function loadPositionContents(position_key) {
  const response = await api.get(`/position/${position_key}`, { params: { search: filter.value } });
  positionContents.value = response.data;

  // Fetch count records for this position and session
  await loadCountRecords(position_key);

  // Auto-select if exactly one item matches the filter
  if (filter.value && response.data.length === 1 && response.data[0].code === filter.value) {
    await nextTick();
    // Check filteredContents after aggregation/processing
    const filtered = filteredContents.value;
    if (filtered.length === 1) {
      // Check if filter matches the item's code (case-insensitive)
      const itemCode = filtered[0].code?.toLowerCase() || '';
      if (itemCode === filter.value.toLowerCase()) {
        selectItem(filtered[0]);
        filter.value = '';
      }
    }
  }
}

async function loadCountRecords(position_key) {
  if (!props.sessionData?._key) return;

  try {
    // The API expects full document IDs (e.g., "Position/KEY") for position_key
    const positionId = position_key.includes('/') ? position_key : `Position/${position_key}`;
    const response = await api.get('/inventory/count-record', {
      params: {
        count_session_key: props.sessionData._key,
        position_key: positionId,
        limit: 1000
      }
    });
    countRecords.value = response.data || [];
  } catch (error) {
    console.error('Error loading count records:', error);
    countRecords.value = [];
  }
}

function selectRootPosition() {
  selectPosition({
    fixed: true,
    _key: 'IN',
    code: 'IN',
  });
}

function selectPosition(position) {
  filter.value = '';
  last_research.value = '';
  selectedPosition.value = position;
  loadPositionContents(position._key);
  stage.value = 'contents';
}

function backToPositionSelection() {
  filter.value = '';
  selectedPosition.value = null;
  positionContents.value = [];
  stage.value = 'position';
}

const filteredContents = computed(() => {
  const search = filter.value || '';

  // 1) Inventory-based items
  const filteredInventory = filterInventoryContents(search);
  const processedInventory = aggregateInventoryItems(filteredInventory);

  // 2) Count-only virtual items (counts without inventory)
  const countOnlyItems = buildCountOnlyItems(search);

  // 3) Combine everything
  const allItems = [
    ...processedInventory.items,
    ...Object.values(processedInventory.serialsByProduct),
    ...countOnlyItems
  ];

  // Sort by code attribute
  return allItems.sort((a, b) => a.code.localeCompare(b.code));
});


onMounted(() => {
  loadLatestUsedPositions();
  loadLatestUsedProducts();
});

function selectItem(item) {
  // Check if item is locked by another user using count records
  const countInfo = getCountInfo(item);
  if (countInfo.hasStarted && countInfo.startedBy) {
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
  const isCounting = countInfo.hasStarted;
  const countBy = countInfo.startedBy || item.count_by || null;

  if (item.type === 'position') {
    selectPosition({ _key: item.position_key, code: item.code });
  } else if (item.isAggregatedSerial) {
    // For aggregated serials, pass the aggregated item with serials array
    selectedItem.value = {
      _key: item._key,
      product_key: item.product_key,
      product_code: item.product_code,
      product_description: item.product_description,
      position_key: selectedPosition.value._key,
      position_code: selectedPosition.value.code,
      serial_key: 'aggregated', // Mark as aggregated
      serials: item.serials,     // Pass all serials for this product
      quantity: item.quantity,
      counting: isCounting,
      count_by: countBy,
      inventory_keys: item.inventory_keys || [],
      path: [{ position_key: selectedPosition.value._key, position_code: selectedPosition.value.code }]
    };
  } else {
    // Convert position API response format to inventory format for counting cards
    selectedItem.value = {
      _key: item._key,
      product_key: item.product_key,
      product_code: item.code,
      product_description: item.product_description,
      position_key: selectedPosition.value._key,
      position_code: selectedPosition.value.code,
      serial_key: item.type === 'serial' ? item.serial_key : null,
      serial_code: item.type === 'serial' ? item.code : null,
      quantity: item.quantity || 0,
      counting: isCounting,
      count_by: countBy,
      inventory_keys: item.inventory_keys || [item._key],
      path: [{ position_key: selectedPosition.value._key, position_code: selectedPosition.value.code }]
    };
  }
}

function unselectItem() {
  console.log('unselectItem');
  selectedItem.value = null;
  loadPositionContents(selectedPosition.value._key);
}

// Helper function to get count records for an item
function getCountRecordsForItem(item) {
  if (!item.product_key) return [];

  const positionKey = selectedPosition.value?._key;
  if (!positionKey) return [];

  return countRecords.value.filter(record => {
    // Extract key from record (handles both "Product/KEY" and "KEY" formats)
    const recordProductKey = record.product_key || (record._from ? record._from.split('/').pop() : null);
    const recordPositionKey = record.position_key || (record._to ? record._to.split('/').pop() : null);

    // For serial items, check if the record matches the product
    if (item.type === 'serial') {
      return recordProductKey === item.product_key && recordPositionKey === positionKey;
    }
    // For product items, match by product_key and position_key
    return recordProductKey === item.product_key && recordPositionKey === positionKey;
  });
}

// Helper function to get count info for display
function getCountInfo(item) {
  const records = getCountRecordsForItem(item);
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

function searchProducts() {
  if (productFilter.value === productLastResearch.value) {
    return;
  }

  if (productFilter.value.length === 0) {
    loadLatestUsedProducts();
    productListLabel.value = 'Recenti';
  } else {
    productLastResearch.value = productFilter.value;
    loading.value = true;
    api.get('product', {
      params: {
        search_string: productFilter.value,
        limit: 100
      }
    }).then((resp) => {
      // Auto-select if exactly one product matches the filter
      if (resp.data.length === 1 && resp.data[0].code === productFilter.value) {
        selectProductForCount(resp.data[0]);
        productFilter.value = '';
      } else {
        productRows.value = resp.data;
      }
      loading.value = false;
      productListLabel.value = 'Risultati';
    });
  }
}

function loadLatestUsedProducts() {
  loading.value = true;
  api.get('movement/latest-products', { params: { limit: 10 } })
    .then((resp) => {
      productRows.value = resp.data;
      loading.value = false;
      productListLabel.value = 'Recenti';
    });
}

function selectProductForCount(product) {
  // Determine card type based on traceability_level
  const isSerialProduct = !!product.traceability_level;

  // Create item object for counting cards
  selectedItem.value = {
    _key: null, // No inventory key yet
    product_key: product._key,
    product_code: product.code,
    product_description: product.description,
    position_key: selectedPosition.value._key,
    position_code: selectedPosition.value.code,
    serial_key: isSerialProduct ? 'aggregated' : null,
    quantity: 0,
    counting: false,
    count_by: null,
    inventory_keys: [], // Empty - item doesn't exist in inventory yet
    path: [{ position_key: selectedPosition.value._key, position_code: selectedPosition.value.code }]
  };

  // Close product search card
  showProductSearch.value = false;
  productFilter.value = '';
}
</script>

<style lang="sass" scoped>
.content-card
  border-radius: 5px
  border: 1px solid transparent

.locked-item
  border: 2px solid var(--theme-blue) !important

.grid-style-transition
  transition: transform .28s, background-color .28s
</style>

