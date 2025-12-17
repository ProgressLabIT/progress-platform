<template>
  <div class="col column">
    <div class="col-auto q-mb-sm text-h3">
      {{ $t('product')}}
    </div>

    <!-- PRODUCT SEARCH -->
    <SearchOrScan v-model="filter" @update:model-value="searchProducts" />

    <!-- PRODUCT LIST -->
    <div class="col-auto q-mt-md q-mb-sm text-h6">
      {{ list_label }} ({{ rows?.length }})
    </div>

    <div class="col scroll column">
      <q-card
        v-for="product in rows"
        :key="product.key"
        v-ripple
        bordered
        flat
        class="surface2 q-px-md q-py-md q-mb-sm"
        @click="selectProduct(product)"
      >
        <div class="text-body1">
          {{ product.code }}
        </div>
        <div class="caption text-low">
          {{ product.description }}
        </div>
      </q-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from 'app/src/boot/axios';
import { useShipmentStore } from '@/stores/shipment';
import SearchOrScan from '@/components/SearchOrScan.vue';
const { t: $t } = useI18n();

const shipment = useShipmentStore();
shipment.$reset()

const list_label = ref('Recenti')
const filter = ref('');
const rows = ref('');
const loading = ref(false);
const last_research = ref(undefined);

function searchProducts() {
  if (filter.value !== last_research.value) {
    if (filter.value === '') {
      loadLatestUsedProducts();
      list_label.value = 'Recenti'
    } else {
      loadProducts(filter);
      list_label.value = 'Risultati'
    }
  }
}

function loadLatestUsedProducts() {
  if (shipment.recentProducts?.length) {
    rows.value = shipment.recentProducts;
  } else {
    loading.value = true;
    api.get('movement/latest-products', { limit: 5 }).then((resp) => {
      shipment.recentProducts = resp.data;
      rows.value = shipment.recentProducts;
      loading.value = false;
    });
  };
}

loadLatestUsedProducts();

function loadProducts(filter) {
  loading.value = true;
  let params = {};

  if (filter.value) {
    params.search_string = filter.value;
    if (rows.value.length === 1 && rows.value[0].code === filter.value) {
      selectProduct(rows.value[0]);
    }
    last_research.value = filter.value;
  }

  params.limit = 100;

  api
    .get('product', {
      params,
    })
    .then((resp) => {
      rows.value = resp.data;
      loading.value = false;
    });
}

function selectProduct(product) {
  shipment.product = product;
  shipment.loadInventory();
  shipment.stage = 'inventory';
}
</script>
