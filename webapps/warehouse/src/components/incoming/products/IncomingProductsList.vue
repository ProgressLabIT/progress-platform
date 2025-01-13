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
// IMPORTS
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from 'app/src/boot/axios';
import { useIncomingStore } from 'app/src/stores/incoming';
import SearchOrScan from '../../SearchOrScan.vue';
const { t: $t } = useI18n();

const incoming = useIncomingStore();
incoming.$reset()

// DATA
const list_label = ref('Recenti')
const filter = ref('');
const rows = ref('');
const loading = ref(false);
const last_research = ref(undefined);

// METHODS
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
  if (incoming.recentProducts?.length) {
    rows.value = incoming.recentProducts;
  } else {
    loading.value = true;
    api.get('movement/latest-products', { limit: 5 }).then((resp) => {
      incoming.recentProducts = resp.data;
      rows.value = incoming.recentProducts;
      loading.value = false;
    });
  };
}

loadLatestUsedProducts();

function loadProducts(filter) {
  loading.value = true;
  let params = {};

  if (filter.value) {
    params.search = filter.value;
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
  incoming.product = product;
  incoming.stage = product.traceability_level ? 'serials' : 'quantity';
}


// LIFECYCLE

</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
