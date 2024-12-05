<template>
  <div class="col column">

    <!-- PRODUCT SEARCH -->
    <SearchOrScan v-model="filter" @update:model-value="searchProducts" />

    <!-- PRODUCT LIST -->
    <div class="col-auto q-mt-lg uppercase text-low">
      Risultati ({{  rows.length }})
    </div>


    <div class="q-mt-md col scroll column">
      <q-card
        v-for="product in rows"
        :key="product.key"
        bordered
        v-ripple
        flat
        class="surface2 q-px-md q-py-md q-mb-sm"
        @click="selectProduct(product)">
        <div class="text-body1">
          {{ product.code }}
        </div>
        <div class="caption text-low">
          {{  product.description }}
        </div>
      </q-card>
    </div>
  </div>
</template>

<script setup>
import { useIncomingStore } from 'app/src/stores/incoming';
import { ref } from 'vue';
import { api as $api } from 'app/src/boot/axios';
import { useRouter } from 'vue-router';
import SearchOrScan from '../../SearchOrScan.vue';


const incoming = useIncomingStore()
const $router = useRouter()

const filter = ref('')
const rows = ref('')
const loading = ref(false)
const last_research = ref(undefined)

function searchProducts() {
  if (filter.value !== last_research.value) {
    loadProducts(filter);
  }
}


function loadProducts(filter) {
  loading.value = true;
  let params = {};

  if (filter.value) {
    params.search = filter.value;
    last_research.value = filter.value;
  }

  params.limit = 100;

  $api
    .get('product', {
      params,
    })
    .then((resp) => {
      rows.value = resp.data;
      loading.value = false;
    });
};

function selectProduct(product) {
  incoming.product = product
  setTimeout(() => $router.push({ name: 'IncomingQuantity'}), 500)
}
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
