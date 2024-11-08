<template>
  <div class="q-pa-md">
    <div class="text-subtitle1 q-py-xl text-center">
      {{ $t('incoming.products.title') }}
    </div>
    <q-table
      flat
      bordered
      grid
      :loading="loading"
      :title="$t('incoming.products.products')"
      :rows="rows"
      :columns="columns"
      row-key="_key"
      :rows-per-page-options="[0]"
      hide-header
    >
      <template #top-right>
        <q-input
          v-model="filter"
          dense
          debounce="300"
          :placeholder="$t('incoming.products.search')"
        >
          <template #append>
            <q-icon name="mdi-magnify" />
            <q-btn
              v-if="false"
              size="0.75rem"
              icon="mdi-barcode-scan"
              @click="show_code_scanner = true"
            >
            </q-btn>
          </template>
        </q-input>
      </template>

      <template #item="{ row }">
        <div
          class="q-pa-xs col-xs-12 col-sm-6 col-md-4 col-lg-3 grid-style-transition"
        >
          <q-card
            v-ripple
            bordered
            flat
            class="my-box cursor-pointer q-hoverable"
            @click="$emit('productSelected', row)"
          >
            <q-card-section>
              <div>{{ row.name }}</div>
            </q-card-section>

            <q-separator />
            <q-list dense>
              <q-item :key="`barcode ${row._key}`">
                <q-item-section side>
                  <q-item-label caption>{{
                    $t('incoming.products.barcode')
                  }}</q-item-label>
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ row.barcode }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item :key="`serial ${row._key}`">
                <q-item-section side>
                  <q-item-label caption>{{
                    $t('incoming.products.serial')
                  }}</q-item-label>
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ row.serial }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-card>
        </div>
      </template>

      <template #no-data> {{ $t('incoming.products.no_data') }}</template>
    </q-table>
  </div>

  <ModalBottomContainer
    :show="show_code_scanner"
    @close="show_code_scanner = false"
  >
    <template #content>
      <CameraCodeScanner @scan="onScan" @load="onLoad"></CameraCodeScanner>
    </template>
  </ModalBottomContainer>
</template>

<script>
import { ref } from 'vue';
import ModalBottomContainer from '@/components/ModalBottomContainer.vue';
import CameraCodeScanner from '@/components/barcode-reader/CameraCodeScanner.vue';

const columns = [
  {
    name: 'name',
    required: true,
    align: 'left',
    field: (row) => row.name,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'barcode',
    required: true,
    align: 'left',
    field: (row) => row.barcode,
    format: (val) => `${val}`,
    sortable: true,
  },
  {
    name: 'serial',
    required: true,
    align: 'left',
    field: (row) => row.serial,
    format: (val) => `${val}`,
    sortable: true,
  },
];

const rows = [
  {
    name: 'Product 1',
    _key: 'PRD 1',
    barcode: '822885026705',
    serial: 'xxxxxx',
  },

  {
    name: 'Product 2',
    _key: 'PRD 2',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 3',
    _key: 'PRD 3',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 4',
    _key: 'PRD 4',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 5',
    _key: 'PRD 5',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 6',
    _key: 'PRD 6',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 7',
    _key: 'PRD 7',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 8',
    _key: 'PRD 8',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 9',
    _key: 'PRD 9',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 10',
    _key: 'PRD 10',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
  },
  {
    name: 'Product 11',
    _key: 'PRD 11',
    barcode: '1231231231231231231',
    serial: 'xxxxxx',
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
      rows,
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
