<template>
  <div class="col column">

    <!-- PRODUCT SEARCH -->
    <div class="row q-col-gutter-sm q-mt-md col-auto">

      <!-- INPUT -->
      <div class="col">
        <q-input
          v-model="filter"
          filled
          autofocus
          debounce="300"
          :label="$t('incoming.products.search')"
          icon="mdi-magnify"
          @update:model-value="searchProducts"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>
      </div>

      <!-- SCAN -->
      <div class="col-auto">
        <q-btn
          class="full-height"
          color="primary"
          size="0.75rem"
          icon="mdi-barcode-scan"
          @click="show_code_scanner = true"
        >
        </q-btn>
      </div>
    </div>

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

    <q-slide-transition>
      <ModalBottomContainer
        :show="show_code_scanner"
        @close="show_code_scanner = false"
      >
        <template #content>
          <CameraCodeScanner @scan="onScan" @load="onLoad"></CameraCodeScanner>
        </template>
      </ModalBottomContainer>
    </q-slide-transition>
  </div>
</template>

<script setup>
import { useIncomingStore } from 'app/src/stores/incoming';
import { ref } from 'vue';
import { api as $api } from 'app/src/boot/axios';
import { useRouter } from 'vue-router';
import ModalBottomContainer from '@/components/ModalBottomContainer.vue';
import CameraCodeScanner from '@/components/barcode-reader/CameraCodeScanner.vue';

const incoming = useIncomingStore()
const $router = useRouter()

const filter = ref('')
const rows = ref('')
const show_code_scanner = ref(false)
const loading = ref(false)
const last_research = ref(undefined)

function searchProducts() {
  if (filter.value !== last_research.value) {
    loadProducts(filter);
  }
}


function onLoad({ controls, scannerElement, browserMultiFormatReader }) {
  console.log(controls);
  console.log(scannerElement);
  console.log(browserMultiFormatReader);
}

function onScan({ result, raw }) {
  filter.value = result;
  console.log(result);
  console.log(raw);
  show_code_scanner.value = false;
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
