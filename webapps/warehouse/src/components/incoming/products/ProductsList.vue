<template>
  <div class="q-px-md q-pt-lg column fit">
    <div class="text-h3 uppercase col-auto text-primary">
      Nuovo Ricevimento
    </div>
    <div class="row q-col-gutter-sm q-mt-md col-auto">
      <div class="col">
        <q-input
          v-model="filter"
          filled
          autofocus
          debounce="300"
          :label="$t('incoming.products.search')"
          icon="mdi-magnify"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
          </template>
        </q-input>
      </div>
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

    <div class="col-auto q-mt-lg uppercase text-low">
      Risultati ({{  rows.length }})
    </div>
    <div class="q-mt-md col scroll q-pb-md column">
      <q-card
        v-for="product in rows"
        :key="product.key"
        bordered
        flat
        class="surface2 q-px-md q-py-md q-mb-sm"
        @click="$emit('productSelected', product)">
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

<script>
import { ref } from 'vue';
import ModalBottomContainer from '@/components/ModalBottomContainer.vue';
import CameraCodeScanner from '@/components/barcode-reader/CameraCodeScanner.vue';

const columns = [
  {
    name: 'code',
    required: true,
    align: 'left',
    field: (row) => row.name,
    format: (val) => `${val}`,
    sortable: true,
  },
  /*{
    name: 'barcode',
    required: true,
    align: 'left',
    field: (row) => row.barcode,
    format: (val) => `${val}`,
    sortable: true,
  },*/
  {
    name: 'description',
    required: true,
    align: 'left',
    field: (row) => row.serial,
    format: (val) => `${val}`,
    sortable: true,
  },
];

const start_rows = [
  {
    code: 'Product 1',
    _key: 'PRD 1',
    barcode: '822885026705',
    description: 'xxxxxx',
  },

  {
    code: 'Product 2',
    _key: 'PRD 2',
    barcode: '1231231231231231231',
    description: 'xxxxxx',
  },
  {
    code: 'Product 3',
    _key: 'PRD 3',
    barcode: '1231231231231231231',
    description: 'xxxxxx',
  },
];

export default {
  name: 'ProductsList',

  components: {
    ModalBottomContainer,
    CameraCodeScanner,
  },

  emits: ['productSelected'],

  setup() {
    return {
      filter: ref(''),
      columns,
      rows: ref(start_rows),
    };
  },

  data() {
    return {
      show_code_scanner: false,
      loading: false,
      last_research: undefined,
    };
  },

  watch: {
    filter: {
      handler() {
        if (this.filter !== this.last_research) {
          this.loadProducts(this.filter);
        }
      },
    },
  },

  methods: {
    onLoad({ controls, scannerElement, browserMultiFormatReader }) {
      console.log(controls);
      console.log(scannerElement);
      console.log(browserMultiFormatReader);
    },
    onScan({ result, raw }) {
      this.filter = result;
      console.log(result);
      console.log(raw);
      this.show_code_scanner = false;
    },
    loadProducts(filter) {
      this.loading = true;
      let params = {};

      if (filter) {
        params.search = filter;
        this.last_research = filter;
      }
      params.limit = 100;

      this.$api
        .get('product', {
          params,
        })
        .then((resp) => {
          this.rows = resp.data;
          this.loading = false;
        });
    },
  },
};
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
