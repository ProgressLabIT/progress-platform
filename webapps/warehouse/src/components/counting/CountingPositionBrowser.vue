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
              :class="[getColor(item), { 'locked-item': item.counting }]"
              @click="selectItem(item)"
            >
              <q-item-section side>
                <q-icon :name="contentIcon[item.type]" />
              </q-item-section>
              <q-item-section>
                <div class="highlight">{{ item.code }}</div>
              </q-item-section>
              <q-item-section v-if="item.quantity && !blindMode" side>
                <div class="text-body2">
                  {{ item.quantity }}
                </div>
              </q-item-section>
              <q-item-section v-if="item.counting" side>
                <q-badge color="yellow" text-color="dark" class="q-pa-xs">
                  <div class="row items-center q-gutter-xs">
                    <span>{{ $t('count_active') }}</span>
                    <BaseUserAvatar
                      v-if="item.count_user"
                      :user="{ _key: item.count_by, ...item.count_user }"
                      :show_name="false"
                      size="20px"
                      dense
                    />
                  </div>
                </q-badge>
              </q-item-section>
            </q-item>
          </q-list>
        </q-scroll-area>
      </template>

      <q-space></q-space>
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
      :blind-mode="blindMode"
      @close="unselectItem()"
    />

    <CountingSerialsCard
      v-if="selectedItem && (selectedItem.serial_key !== null || selectedItem.serial_key === 'aggregated')"
      :item="selectedItem"
      :blind-mode="blindMode"
      @close="unselectItem()"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
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

const blindMode = computed(() => props.sessionData.blind_mode);

const contentIcon = {
  product: 'mdi-apps',
  serial: 'mdi-cube-scan',
  position: 'mdi-package-variant-closed',
};

function getColor(item) {
  const colorMap = {
    product: 'blue',
    serial: 'green',
    position: 'red'
  };
  const color = colorMap[item.type];
  return `bg-${color}-backdrop`;
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

  if (filter.value.length === 0) {
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
  // First filter items based on search
  const filtered = positionContents.value.filter(item => {
    const searchContext = item.code + ' ' + item.product_code;
    return searchContext.toLowerCase().includes(filter.value.toLowerCase());
  });

  // Process all items in a single reduce, creating uniform data model
  const processedItems = filtered.reduce((acc, item) => {
    if (item.type === 'serial') {
      // Serial items: aggregate by product_key
      const key = item.product_key;
      if (!acc.serialsByProduct[key]) {
        acc.serialsByProduct[key] = {
          _key: `aggregated_${item.product_key}`,
          type: 'serial',
          code: item.product_code,
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
      // If multiple users, don't show as locked (shouldn't happen per requirements)
    }
    // Clean up temporary tracking field
    delete aggregated.counting_items;
  });

  // Combine direct items with aggregated serials
  const allItems = [
    ...processedItems.items,
    ...Object.values(processedItems.serialsByProduct)
  ];

  // Sort by code attribute
  return allItems.sort((a, b) => a.code.localeCompare(b.code));
});

onMounted(() => {
  loadLatestUsedPositions();
});

function selectItem(item) {
  // Check if item is locked by another user
  if (item.counting && item.count_by) {
    const currentUserKey = store.state.session.user._key;
    if (item.count_by !== currentUserKey) {
      // Item is locked by another user, block access
      Notify.create({
        message: $t('count_locked_by_other_user'),
        color: 'negative',
        position: 'top',
        timeout: 3000
      });
      return;
    }
    // Item is locked by current user, proceed normally
  }

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
      serials: item.serials, // Pass all serials for this product
      quantity: item.quantity,
      counting: item.counting || false,
      count_by: item.count_by || null,
      inventory_keys: item.inventory_keys || [],
      path: [{ position_key: selectedPosition.value._key, position_code: selectedPosition.value.code }]
    };
  } else {
    // Convert position API response format to inventory format for counting cards
    selectedItem.value = {
      _key: item._key,
      product_key: item.product_key,
      product_code: item.product_code,
      product_description: item.product_description,
      position_key: selectedPosition.value._key,
      position_code: selectedPosition.value.code,
      serial_key: item.type === 'serial' ? item.serial_key : null,
      serial_code: item.type === 'serial' ? item.code : null,
      quantity: item.quantity || 0,
      counting: item.counting || false,
      count_by: item.count_by || null,
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
</script>

<style lang="sass" scoped>
.content-card
  border-radius: 5px

.locked-item
  border: 2px solid yellow !important

.grid-style-transition
  transition: transform .28s, background-color .28s
</style>

