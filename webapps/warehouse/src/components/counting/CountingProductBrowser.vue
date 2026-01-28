<template>
  <div class="col column q-gutter-y-md">
    <!-- STATE 1: Product Selection -->
    <template v-if="!selectedProduct">
      <div class="col-auto q-mb-sm text-h3">
        {{ $t('product') }}
      </div>

      <!-- PRODUCT SEARCH -->
      <SearchOrScan v-model="productFilter" @update:model-value="searchProducts" />

      <!-- PRODUCT LIST -->
      <div class="col-auto q-mt-md q-mb-sm text-h6">
        {{ productListLabel }} ({{ productRows?.length || 0 }})
      </div>

      <CountingProductList
        :products="productRows"
        class="col"
        @select="selectProduct"
      />
    </template>

    <!-- STATE 2: Contents View for Selected Product -->
    <template v-else>
      <!-- Navigation Header -->
      <div class="row items-center q-gutter-x-sm">
        <div class="col-auto">
        <div class="text-h5 text-uppercase text-low">
          {{ $t('product') }}
        </div>
        <div class="text-h3 text-uppercase highlight">
          {{ selectedProduct.code }}
        </div>
        <div class="text-body2">
          {{ selectedProduct.description }}
        </div>
        </div>
        <q-space />
        <div class="col-auto items-bottom">
        <q-btn
          size="sm"
          dense
          flat
          color="theme-grey"
          :label="$t('reset')"
          label-left
          icon-right="mdi-close-circle"
          @click="resetProductSelection"
        />
        </div>
      </div>

      <!-- Counting Contents -->
      <CountingContentsView
        ref="contentsViewRef"
        :session-data="sessionData"
        :contents="positionContents"
        :count-records="countRecords"
        :position-status="{}"
        :position-key="null"
        :product-key="selectedProduct?._key"
        :loading="loading"
        class="col"
        @refresh-position="loadProductInventory"
      />
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';
import { Loading } from 'quasar';
import SearchOrScan from '@/components/SearchOrScan.vue';
import CountingProductList from './CountingProductList.vue';
import CountingContentsView from './CountingContentsView.vue';

const props = defineProps({
  sessionData: {
    type: Object,
    required: true
  }
});

const { t: $t } = useI18n();

// Product selection state
const selectedProduct = ref(null);
const productFilter = ref('');
const productListLabel = ref('Recenti');
const productRows = ref([]);
const productLastResearch = ref(undefined);

// Contents view state
const positionContents = ref([]);
const countRecords = ref([]);
const loading = ref(false);
const contentsViewRef = ref(null);

// Load recent products on mount
loadRecentProducts();

async function loadRecentProducts() {
  Loading.show();
  try {
    const resp = await api.get('movement/latest-products', {
      params: { limit: 10 }
    });
    productRows.value = resp.data;
    productListLabel.value = $t('recent');
  } catch (error) {
    console.error('Error loading recent products:', error);
    productRows.value = [];
  } finally {
    Loading.hide();
  }
}

async function searchProducts() {
  if (productFilter.value === productLastResearch.value) {
    return;
  }

  if (!productFilter.value) {
    await loadRecentProducts();
    productLastResearch.value = '';
    return;
  }

  Loading.show();
  try {
    const resp = await api.get('product', {
      params: {
        search_string: productFilter.value,
        limit: 100
      }
    });
    productRows.value = resp.data;
    productListLabel.value = $t('results');
    productLastResearch.value = productFilter.value;

    // Auto-select if exact match
    if (productRows.value.length === 1 && productRows.value[0].code === productFilter.value) {
      selectProduct(productRows.value[0]);
      productFilter.value = '';
    }
  } catch (error) {
    console.error('Error searching products:', error);
    productRows.value = [];
  } finally {
    Loading.hide();
  }
}

async function selectProduct(product) {
  selectedProduct.value = product;
  await loadProductInventory();
}

async function loadProductInventory() {
  if (!selectedProduct.value) return;

  loading.value = true;
  Loading.show();

  try {
    // Load inventory for the selected product
    const inventoryResp = await api.get('inventory', {
      params: {
        product_key: selectedProduct.value._key,
        limit: 0
      }
    });

    // Transform inventory items to contents format expected by CountingContentsView
    positionContents.value = (inventoryResp.data || []).map(item => ({
      _key: item._key,
      type: item.serial_key ? 'serial' : 'product',
      code: item.serial_key ? item.serial_code : item.product_code,
      product_key: item.product_key,
      product_code: item.product_code,
      product_description: item.product_description,
      position_key: item.position_key,
      position_code: item.position_code,
      serial_key: item.serial_key || null,
      serial_code: item.serial_code || null,
      quantity: item.quantity,
      path: item.path || []
    }));

    // Load count records for this session and product
    const countResp = await api.get('/inventory/count-record', {
      params: {
        count_session_key: props.sessionData._key,
        product_key: selectedProduct.value._key,
        limit: 0
      }
    });
    countRecords.value = countResp.data || [];

  } catch (error) {
    console.error('Error loading product inventory:', error);
    positionContents.value = [];
    countRecords.value = [];
  } finally {
    loading.value = false;
    Loading.hide();
  }
}

function resetProductSelection() {
  selectedProduct.value = null;
  positionContents.value = [];
  countRecords.value = [];
  productFilter.value = '';
}
</script>

<style lang="scss" scoped>
</style>
