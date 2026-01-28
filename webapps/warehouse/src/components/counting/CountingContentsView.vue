<template>
  <div class="col column">
    <!-- SEARCH / FILTER -->
    <SearchOrScan
      v-model="filter"
      class="q-mb-sm"
    />

    <!-- HEADER + HIDE COUNTED -->
    <div class="row items-center justify-between q-mb-sm">
      <div class="text-h6">
        {{ !loading && contents.length === 0 ? $t('no_contents') : $t('contents') }}
      </div>
      <q-checkbox
        v-model="hideCountedFilter"
        left-label
        dense
        :label="$t('hide_counted')"
        :disable="loading"
        class="text-body2"
      />
    </div>

    <!-- ITEMS LIST -->
    <q-virtual-scroll
      :items="filteredContents"
      v-slot="{ item }"
      class="col q-mb-md thin-scrollbar"
    >
      <q-item
        :key="item._key"
        clickable
        class="content-card q-my-xs q-py-sm text-body1"
        style="height: 75px; max-width: 95vw"
        :style="{ 'border-color': getCountInfo(item).hasStarted ? 'var(--theme-blue)' : null }"
        :class="[
          getColor(item),
          {
            'locked-item':
              getCountInfo(item).hasStarted &&
              getCountInfo(item).startedBy === store.state.session.user._key
          }
        ]"
        @click="handleItemClick(item)"
      >
        <!-- ICON -->
        <q-item-section side class="col-auto">
          <q-icon :name="contentIcon[item.type]" />
        </q-item-section>

        <!-- CODE AND DESCRIPTION -->
        <q-item-section>
          <div class="row items-center highlight">
            <div class="col-auto q-mr-sm">{{ item.code }}</div>

            <!-- Count-only Icon -->
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
                :name="
                  getCountInfo(item).startedBy === store.state.session.user._key
                    ? 'mdi-progress-pencil'
                    : 'mdi-lock'
                "
                :color="
                  getCountInfo(item).startedBy === store.state.session.user._key
                    ? 'theme-blue'
                    : 'theme-orange'
                "
                size="16px"
              />
            </div>

            <!-- Completed Icon -->
            <div class="col-auto column items-center">
              <q-icon
                v-if="
                  getCountInfo(item).completedCount > 0 &&
                  !(getCountInfo(item).hasStarted &&
                    getCountInfo(item).startedBy === store.state.session.user._key)
                "
                name="mdi-check-circle"
                color="theme-green"
                size="16px"
              />
            </div>
          </div>
          <q-item-label v-if="item.product_description && sessionData.type === 'position'" caption lines="2">
            {{ item.product_description }}
          </q-item-label>
          <q-item-label v-if="sessionData.type === 'product'" caption lines="2">
            {{ getPathString(item) }}
          </q-item-label>
        </q-item-section>

        <!-- QUANTITY -->
        <q-item-section v-if="item.quantity && !blindQuantities" side class="col-auto">
          <div class="text-body2">
            {{ Math.round(item.quantity * 10 ** 4) / 10 ** 4 }}
            <span v-if="getCountedQuantity(item) !== null" class="text-low q-ml-xs">
              / {{ getCountedQuantity(item) }}
            </span>
          </div>
        </q-item-section>

        <!-- COUNTED QUANTITY (blind mode) -->
        <q-item-section
          v-if="blindQuantities && getCountedQuantity(item) !== null"
          side
          class="col-auto"
        >
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
            <q-icon
              name="mdi-check-circle"
              :size="positionStatus[item.position_key] === 'empty' ? '10px' : '25px'"
            />
            <q-icon
              v-if="positionStatus[item.position_key] === 'empty'"
              name="mdi-package-variant-remove"
              size="27px"
            />
          </div>
        </q-item-section>

        <!-- COUNT NUMBER & USER -->
        <q-item-section
          v-if="
            getCountInfo(item).hasRecords &&
            (getCountInfo(item).startedBy || getCountInfo(item).completedBy.length > 0)
          "
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

    <!-- COUNTING CARDS -->
    <CountingQuantityCard
      v-if="selectedItem && selectedItem.serial_key === null"
      :item="selectedItem"
      @close="handleCountingClosed"
    />

    <CountingSerialsCard
      v-if="selectedItem && selectedItem?.serial_key !== null"
      :item="selectedItem"
      :blind-mode="blindSerials"
      @close="handleCountingClosed"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, defineExpose } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { api } from '@/boot/axios';
import { store } from '@/boot/store';
import SearchOrScan from '@/components/SearchOrScan.vue';
import CountingQuantityCard from './CountingQuantityCard.vue';
import CountingSerialsCard from './CountingSerialsCard.vue';
import BaseUserAvatar from '@/components/BaseUserAvatar.vue';

const props = defineProps({
  sessionData: {
    type: Object,
    required: true
  },
  // Raw contents for the current context (position or product-based)
  contents: {
    type: Array,
    required: true
  },
  // Count records for the current context (typically per position)
  countRecords: {
    type: Array,
    default: () => []
  },
  // Map of position_key -> status ('empty' | 'checked' | ...)
  positionStatus: {
    type: Object,
    default: () => ({})
  },
  // Optional position context (for position-based sessions)
  positionKey: {
    type: String,
    default: null
  },
  // Optional product context (for product-based sessions)
  productKey: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['position-selected', 'refresh-position']);

const { t: $t } = useI18n();

const filter = ref('');
const hideCountedFilter = ref(false);
const selectedItem = ref(null);
const usersByKeys = ref({});

// Load users once for avatars
api.get('user').then((resp) => {
  usersByKeys.value = resp.data.detail.reduce((acc, user) => {
    acc[user._key] = user;
    return acc;
  }, {});
});

const blindQuantities = computed(() => props.sessionData.blind_quantities ?? true);
const blindSerials = computed(() => props.sessionData.blind_serials ?? true);

const contentIcon = {
  product: 'mdi-apps',
  serial: 'mdi-cube-scan',
  position: 'mdi-package-variant-closed'
};

function getColor(item) {
  if (item && item.isCountOnly) {
    // Count-only items are rendered as outline-only, without background color
    return 'bg-grey-backdrop';
  }
  const colorMap = {
    product: 'blue',
    serial: 'green',
    position: 'red'
  };
  const color = colorMap[item.type];
  return `bg-${color}-backdrop`;
}

// --- Helpers for filtered contents ---

function getPathString(item) {
  return item.path?.map(p => p.position_code).join(' → ') || 'IN';
}

function aggregateInventoryItems(filteredItems) {
  // Process all inventory items in a single reduce, creating uniform data model
  const aggregateKey = props.sessionData.type === 'product' ? 'position_key' : 'product_key';
  const processedItems = filteredItems.reduce(
    (acc, item) => {
      if (item.type === 'serial') {
        // Serial items: aggregate by product_key
        const key = item[aggregateKey];
        if (!acc.serialsByProduct[key]) {
          acc.serialsByProduct[key] = {
            _key: `aggregated_${item[aggregateKey]}`,
            type: 'serial',
            code: item.product_code,
            product_description: item.product_description,
            product_key: item.product_key,
            position_key: item.position_key,
            position_code: item.position_code,
            path: item.path,
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
    },
    { items: [], serialsByProduct: {} }
  );

  // Process aggregated serials to determine if they're all locked by the same user
  Object.keys(processedItems.serialsByProduct).forEach((key) => {
    const aggregated = processedItems.serialsByProduct[key];
    // Check if ALL serials are locked and by the same user
    const allLocked = aggregated.counting_items.every((item) => item.counting === true);
    if (allLocked && aggregated.counting_items.length > 0) {
      // Check if all are locked by the same user
      const uniqueCountBy = new Set(
        aggregated.counting_items.map((i) => i.count_by).filter(Boolean)
      );
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
  const sessionType = props.sessionData.type;
  const contextKey = sessionType === 'product' ? props.productKey : props.positionKey;

  if (!contextKey) {
    return [];
  }

  // Product-based sessions: show positions where this product was counted but has no inventory
  if (sessionType === 'product') {
    const inventoryPositionKeys = new Set(
      props.contents.map((item) => item.position_key).filter(Boolean)
    );

    const countOnlyMap = new Map();

    props.countRecords.forEach((record) => {
      const recordProductKey =
        record.product_key || (record._from ? record._from.split('/').pop() : null);
      if (recordProductKey !== contextKey) {
        return;
      }

      const recordPositionKey =
        record.position_key || (record._to ? record._to.split('/').pop() : null);
      if (!recordPositionKey || inventoryPositionKeys.has(recordPositionKey)) {
        return;
      }

      const aggregateKey = `${contextKey}_${recordPositionKey}`;
      if (!countOnlyMap.has(aggregateKey)) {
        countOnlyMap.set(aggregateKey, {
          _key: `count_only_${aggregateKey}`,
          type: 'product',
          code: record.position_code || recordPositionKey,
          product_key: contextKey,
          position_key: recordPositionKey,
          position_code: record.position_code || null,
          path: record.position_path
            ? record.position_path.map((code, index) => ({
                position_code: code,
                position_key: record.position_path_keys?.[index]
              }))
            : [],
          quantity: null,
          inventory_keys: [],
          isCountOnly: true
        });
      }
    });

    return Array.from(countOnlyMap.values());
  }

  // Position-based sessions: keep existing logic (products counted without inventory in this position)
  const inventoryProductKeys = new Set(
    props.contents.map((item) => item.product_key).filter(Boolean)
  );

  const countOnlyMap = new Map();

  props.countRecords.forEach((record) => {
    const productKey = record.product_key;
    if (!productKey || inventoryProductKeys.has(productKey)) {
      // Skip products that already have inventory in this position
      return;
    }

    // Ensure record belongs to the current positionKey (document id or key)
    const recordPositionKeyRaw = record.position_key || (record._to ? record._to : null);
    const recordPositionKey = recordPositionKeyRaw && recordPositionKeyRaw.includes('/')
      ? recordPositionKeyRaw.split('/').pop()
      : recordPositionKeyRaw;

    if (recordPositionKey && recordPositionKey !== contextKey) {
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
        position_key: recordPositionKey || contextKey,
        position_code: null,
        quantity: null, // No system quantity for virtual items
        inventory_keys: [], // No inventory backing
        isCountOnly: true, // Flag for outline-only rendering
        traceability_level: record.product_traceability_level || null
      });
    }
  });

  return Array.from(countOnlyMap.values());
}

// Helper: Group count records by product/position depending on session type
function groupRecordsByContext(records, contextKey, sessionType) {
  return records.reduce((acc, record) => {
    const recordProductKey =
      record.product_key || (record._from ? record._from.split('/').pop() : null);
    const recordPositionKey =
      record.position_key || (record._to ? record._to.split('/').pop() : null);

    // For position-based: filter by position, group by product
    // For product-based: filter by product, group by position
    const filterKey = sessionType === 'product' ? recordProductKey : recordPositionKey;
    const groupKey = sessionType === 'product' ? recordPositionKey : recordProductKey;

    if (groupKey && filterKey === contextKey) {
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
  const completedRecords = records.filter(
    (r) => r.status === 'completed' || r.status === 'submitted' || r.status === 'confirmed'
  );
  const startedRecords = records.filter((r) => r.status === 'started');

  return {
    hasRecords: records.length > 0,
    completedCount: completedRecords.length,
    startedCount: startedRecords.length,
    hasStarted: startedRecords.length > 0,
    startedBy: startedRecords.length > 0 ? startedRecords[0].user_key : null,
    completedBy: [...new Set(completedRecords.map((r) => r.user_key).filter(Boolean))],
    allRecords: records
  };
}

// Helper: Build count info map from items and grouped records
function buildCountInfoMap(items, recordsByKey, contextKey, sessionType) {
  return items.reduce((map, item) => {
    if (!item.product_key) {
      return map;
    }

    const positionKeyForItem =
      sessionType === 'product' ? item.position_key : contextKey;
    const key = `${item.product_key}_${positionKeyForItem}`;
    const records = recordsByKey.get(key) || [];
    map.set(item._key, buildCountInfoForItem(item, records));

    return map;
  }, new Map());
}

// Pre-compute count info map for all items to avoid repeated filtering
const countInfoMap = computed(() => {
  const sessionType = props.sessionData.type;
  const contextKey = sessionType === 'product' ? props.productKey : props.positionKey;

  if (!contextKey || !props.countRecords.length) {
    return new Map();
  }

  // Pre-process count records by product_key + position_key for faster lookup
  const recordsByKey = groupRecordsByContext(props.countRecords, contextKey, sessionType);

  // Get all items that could appear in filteredContents (before text filtering)
  const processedInventory = aggregateInventoryItems(props.contents);
  const countOnlyItems = buildCountOnlyItems();
  const allItems = [
    ...processedInventory.items,
    ...Object.values(processedInventory.serialsByProduct),
    ...countOnlyItems
  ];

  // Build count info for each item
  return buildCountInfoMap(allItems, recordsByKey, contextKey, sessionType);
});

const filteredContents = computed(() => {
  const searchLower = (filter.value || '').toLowerCase();

  // 1) Inventory-based items - aggregate serials by product
  const processedInventory = aggregateInventoryItems(props.contents);

  // 2) Count-only virtual items (counts without inventory)
  const countOnlyItems = buildCountOnlyItems();

  // 3) Combine everything
  const allItems = [
    ...processedInventory.items,
    ...Object.values(processedInventory.serialsByProduct),
    ...countOnlyItems
  ];

  // 4) Apply text filter to all items
  const textFiltered = searchLower
    ? allItems.filter((item) => {
        const code = (item.code || '').toLowerCase();
        const description = (item.product_description || '').toLowerCase();
        const searchContext = `${code} ${description}`;
        return searchContext.includes(searchLower);
      })
    : allItems;

  // 5) Filter out completed counts if hideCountedFilter is active
  const filteredItems = hideCountedFilter.value
    ? textFiltered.filter((item) => {
        // Filter out items with completed counts
        const countInfo = countInfoMap.value.get(item._key);
        if (countInfo && countInfo.completedCount > 0) {
          return false;
        }
        // Filter out positions that are counted or empty
        if (item.type === 'position' && item.position_key && item.position_key in props.positionStatus) {
          return false;
        }
        return true;
      })
    : textFiltered;

  // 6) Sort by code attribute
  return filteredItems.sort((a, b) => a.code.localeCompare(b.code));
});

// Auto-select item if exactly one matches the filter
watch(filteredContents, async (filtered) => {
  if (filter.value && filtered.length === 1) {
    // Check if filter matches the item's code exactly (case-insensitive)
    const itemCode = filtered[0].code?.toLowerCase() || '';
    if (itemCode === filter.value.toLowerCase()) {
      await nextTick();
      handleItemClick(filtered[0]);
      filter.value = '';
    }
  }
});

function handleItemClick(item) {
  // Positions: delegate navigation to parent
  if (item.type === 'position' && item.position_key) {
    emit('position-selected', item.position_key);
    return;
  }

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

  if (item.isAggregatedSerial) {
    // For aggregated serials, pass the aggregated item with serials array
    selectedItem.value = {
      _key: item._key,
      product_key: item.product_key,
      product_code: item.product_code,
      product_description: item.product_description,
      position_key: props.positionKey,
      position_code: null,
      serial_key: 'aggregated', // Mark as aggregated
      serials: item.serials, // Pass all serials for this product
      quantity: item.quantity,
      counting: isCounting,
      count_by: countBy,
      inventory_keys: item.inventory_keys || [],
      path: [],
      lastCountRecord
    };
  } else {
    // Convert position API response format to inventory format for counting cards
    selectedItem.value = {
      _key: item._key,
      product_key: item.product_key,
      product_code: item.code,
      product_description: item.product_description,
      position_key: props.positionKey || item.position_key || null,
      position_code: item.position_code || null,
      serial_key: item.type === 'serial' ? item.serial_key : null,
      serial_code: item.type === 'serial' ? item.code : null,
      quantity: item.quantity || 0,
      counting: isCounting,
      count_by: countBy,
      inventory_keys: item.inventory_keys || [item._key],
      path: item.path || [],
      lastCountRecord
    };
  }
}

function handleCountingClosed() {
  selectedItem.value = null;
  emit('refresh-position');
}

// Helper function to get count info for display (uses pre-computed map)
function getCountInfo(item) {
  return (
    countInfoMap.value.get(item._key) || {
      hasRecords: false,
      completedCount: 0,
      startedCount: 0,
      hasStarted: false,
      startedBy: null,
      completedBy: [],
      allRecords: []
    }
  );
}

// Helper function to get counted quantity from count records
function getCountedQuantity(item) {
  const lastRecord = getLastCountRecord(item);
  return Math.round((lastRecord?.counted_qt ?? 0) * 10 ** 4) / 10 ** 4;
}

// Helper function to get the last completed count record (from any user)
function getLastCountRecord(item) {
  const countInfo = getCountInfo(item);
  if (!countInfo.hasRecords || countInfo.allRecords.length === 0) {
    return null;
  }

  // Get completed/submitted/confirmed records from any user
  const completedRecords = countInfo.allRecords.filter(
    (r) => r.status === 'completed' || r.status === 'submitted' || r.status === 'confirmed'
  );

  if (completedRecords.length === 0) {
    return null;
  }

  // Sort by counted_at descending and return the most recent
  return completedRecords.sort((a, b) => {
    const dateA = a.counted_at ? new Date(a.counted_at) : new Date(0);
    const dateB = b.counted_at ? new Date(b.counted_at) : new Date(0);
    return dateB - dateA;
  })[0];
}

// Allow parent to open counting cards directly (e.g. from product search)
function openForProduct(product, positionKey = null, positionCode = null) {
  selectedItem.value = {
    _key: null, // No inventory key yet
    product_key: product._key,
    product_code: product.code,
    product_description: product.description,
    position_key: positionKey,
    position_code: positionCode,
    serial_key: product.traceability_level ? 'aggregated' : null,
    quantity: 0,
    counting: false,
    count_by: null,
    inventory_keys: [], // Empty - item doesn't exist in inventory yet
    path: positionKey && positionCode ? [{ position_key: positionKey, position_code: positionCode }] : []
  };
}

defineExpose({
  openForProduct
});
</script>

<style lang="sass" scoped>
.content-card
  border-radius: 5px

.locked-item
  border: 2px solid var(--theme-blue) !important

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

