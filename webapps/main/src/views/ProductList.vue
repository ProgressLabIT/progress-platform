<template>
  <q-page-container class="q-pa-md" style="height: 100vh">
    <q-page class="fit column">
      <!-- Header row with product filter and view controls -->
      <div class="col-auto q-py-md row q-col-gutter-lg items-center">
        <div class="col-12 col-sm-5 col-md-3">
          <q-input
            v-model="search_string"
            dense
            filled
            hide-bottom-space
            autocomplete="off"
            name="search"
            :placeholder="$t('search')"
            input-class="text-uppercase text-body1"
            :debounce="300"
          >
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>
        </div>

        <div class="col-12 col-sm-5 col-md-3">
          <!-- TAG -->
          <BaseAutocompleteTag
            dense
            key-only
            :label="$t('tag')"
            :value="tag_key"
            @select="(selection) => (tag_key = selection)"
          />
        </div>

        <!-- View controls -->
        <q-checkbox
          v-model="search_description"
          class="col-auto text-body1 low-text"
          :label="$capitalize($t('product.filters.search_description'))"
        />
        <q-checkbox
          v-model="active_only"
          class="col-auto text-body1 low-text"
          :label="$capitalize($t('product.filters.active_only'))"
        />
        <q-checkbox
          v-model="show_images"
          class="col-auto text-body1 low-text"
          :label="$capitalize($t('product.filters.show_images'))"
        />

        <q-space />

        <div class="col-auto">
          <q-btn
            flat
            dense
            icon="mdi-upload"
            :label="$t('product.import.import')"
            @click="showImportDialog = true"
          />
        </div>

        <div class="col-auto">
          <q-btn-dropdown
            :loading="exporting"
            icon="mdi-download"
            flat
            dense
            :label="$t('export')"
          >
            <q-list>
              <q-item v-close-popup clickable @click="exportProducts(filters, 'xlsx')">
                <q-item-section>{{ $t('product.export_xlsx') }}</q-item-section>
              </q-item>
              <q-item v-close-popup clickable @click="exportProducts(filters, 'csv')">
                <q-item-section>{{ $t('product.export_csv') }}</q-item-section>
              </q-item>
              <q-item v-close-popup clickable @click="exportProducts(filters, 'template')">
                <q-item-section>{{ $t('product.export_template') }}</q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>

        <div class="col-auto">
          <q-btn
            color="theme-blue"
            @click="$router.push({ name: 'newProduct' })"
          >
            {{ $t('new') }}
          </q-btn>
        </div>
      </div>

      <!-- PRODUCT LIST -->
      <div id="product-list" class="col scroll flex-center">
        <div v-if="vuex_ready" class="row q-col-gutter-lg q-mb-md">
          <NoDataAlert v-if="!productCatalog().length" />
          <div
            v-for="(product, index) in productCatalog()"
            :key="index"
            class="col-12 col-sm-6 col-md-3 col-xl-2"
            :style="`height: ${card_height}px`"
          >
            <ProductCard
              :key="product._key"
              :product="product"
              :show-image="show_images"
            />
          </div>
        </div>
        <div class="row q-my-lg justify-center">
          <q-btn
            v-if="load_quantity + offset <= productCatalog().length"
            flat
            color="theme-blue"
            @click="showMore"
          >
            {{ $t('load_more') }}
          </q-btn>
          <q-spinner v-if="loading" />
        </div>
      </div>

      <ProductImportDialog
        v-model="showImportDialog"
        @imported="fetchProducts"
      />

      <router-view />
    </q-page>
  </q-page-container>
</template>

<script>
import { mapGetters } from 'vuex';
import BaseAutocompleteTag from '@/components/BaseAutocompleteTag.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import ProductCard from '@/components/ProductCard.vue';
import ProductImportDialog from '@/components/ProductImportDialog.vue';
import { useProductExport } from '@/composables/useProductExport';
import { useProductImport } from '@/composables/useProductImport';
import multiMatch from '@/lib/MultiFieldSearch.js';
import queryModel from '@/lib/queryModelFactory.js';

export default {
  name: 'ProductList',

  components: {
    NoDataAlert,
    ProductCard,
    BaseAutocompleteTag,
    ProductImportDialog,
  },

  setup() {
    return { ...useProductExport(), ...useProductImport() }
  },

  data() {
    return {
      // search_string: null,
      loading: false,
      vuex_ready: false,
      load_quantity: 100,
      offset: 0,
    };
  },

  computed: {
    ...mapGetters(['productCatalog']),

    max_shown() {
      return this.load_quantity + this.offset;
    },

    search_string: queryModel(String, 'search_string', null),
    search_description: queryModel(Boolean, 'search_description', false),
    tag_key: queryModel(String, 'tag_key', null),
    active_only: queryModel(Boolean, 'active_only', false),
    show_images: queryModel(Boolean, 'show_images', false),

    filters() {
      return {
        limit: this.load_quantity,
        offset: this.offset,
        search_code: this.search_code,
        search_description: this.search_description,
        active_only: this.active_only,
        tag_key: this.tag_key,
        search_string: this.search_string,
      };
    },

    card_height() {
      return this.show_images ? 240 : 150;
    },
  },

  watch: {
    search_string: {
      handler: 'fetchProducts',
    },

    active_only: {
      handler: 'fetchProducts',
    },

    tag_key: {
      handler: 'fetchProducts',
    },

    search_code: {
      handler: 'fetchProducts',
    },

    search_description: {
      handler: 'fetchProducts',
    },
  },

  created() {
    this.fetchProducts().then(() => {
      this.vuex_ready = true;
    });
  },

  methods: {
    fetchProducts() {
      return new Promise((resolve) => {
        this.loading = true;
        this.offset = 0;
        this.$store.dispatch('loadProductList', this.filters).then(() => {
          setTimeout(() => (this.loading = false), 2000);
          resolve();
        });
      });
    },

    match(product) {
      return multiMatch(this.search_string, product, [
        'code',
        'description',
        ['tags', 'name'],
      ]);
    },

    showMore() {
      this.loading = true;
      this.offset += this.load_quantity;
      this.$store.dispatch('appendProductList', this.filters).then(() => {
        setTimeout(() => (this.loading = false), 700);
        this.vuex_ready = true;
      });
    },
  },
};
</script>
