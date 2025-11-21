<template>
  <div class="col column q-gutter-y-md">
    <!-- Search/Filter -->
    <SearchOrScan v-model="productSearch" :label="$t('search_product')" class="q-mb-md" />

    <!-- Product List -->
    <div v-if="inventory.contents.length === 0" class="text-h6">{{ $t('no_results') }}</div>

    <q-scroll-area v-else class="col">
      <q-list>
        <q-item
          v-for="item in filteredContents"
          :key="item._key"
          clickable
          class="content-card q-my-sm q-pa-md text-body1"
          :class="backgroundClass(item)"
          @click="onItemClick(item)"
        >
          <q-item-section side>
            <q-icon :name="item.serial_key ? 'mdi-cube-scan' : 'mdi-apps'" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="highlight">
              {{ item.serial_code ? item.serial_code : item.product_code }}
            </q-item-label>
            <q-item-label caption>
              {{ item.product_description }}
            </q-item-label>
            <q-item-label caption>
              {{ item.path.map(p => p.position_code).join(' → ') || 'IN' }}
            </q-item-label>
          </q-item-section>
          <q-item-section v-if="item.serial_key === null && !blindMode" side>
            <div class="text-body2">
              {{ item.quantity }}
            </div>
          </q-item-section>
        </q-item>
      </q-list>
    </q-scroll-area>

    <!-- Counting Cards -->
    <CountingQuantityCard
      v-if="selectedItem && selectedItem.serial_key === null"
      :item="selectedItem"
      :blind-mode="blindMode"
      @close="selectedItem = null"
    />

    <CountingSerialsCard
      v-if="selectedItem && selectedItem.serial_key !== null"
      :item="selectedItem"
      :blind-mode="blindMode"
      @close="selectedItem = null"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useInventoryStore } from '@/stores/inventory';
import SearchOrScan from '@/components/SearchOrScan.vue';
import CountingQuantityCard from './CountingQuantityCard.vue';
import CountingSerialsCard from './CountingSerialsCard.vue';

const props = defineProps({
  sessionData: {
    type: Object,
    required: true
  }
});

const { t: $t } = useI18n();
const inventory = useInventoryStore();
const productSearch = ref('');
const selectedItem = ref(null);

const blindMode = computed(() => props.sessionData.blind_mode);

const filteredContents = computed(() => {
  if (!productSearch.value) return inventory.contents;
  const search = productSearch.value.toLowerCase();
  return inventory.contents.filter(item => {
    const productCode = item.product_code?.toLowerCase() || '';
    const productDesc = item.product_description?.toLowerCase() || '';
    const serialCode = item.serial_code?.toLowerCase() || '';
    return productCode.includes(search) || productDesc.includes(search) || serialCode.includes(search);
  });
});

function backgroundClass(item) {
  const color = item.serial_key ? 'green' : 'blue';
  return `bg-${color}-backdrop`;
}

function onItemClick(item) {
  selectedItem.value = item;
}

onMounted(() => {
  // Load all inventory for the counting session
  // In a real implementation, this would be filtered by the session's assigned products
  inventory.loadInventory({});
});
</script>

<style lang="scss" scoped>
.content-card {
  border-radius: 5px;
}
</style>

