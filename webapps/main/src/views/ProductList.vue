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

        <!-- View controls -->
        <q-checkbox
          v-model="filter_inactive"
          class="col-auto text-body1 low-text"
          :label="$capitalize($t('product.filters.active_only'))"
        >
        </q-checkbox>
        <q-checkbox
          v-model="show_images"
          class="col-auto text-body1 low-text"
          :label="$capitalize($t('product.filters.show_images'))"
        >
        </q-checkbox>

        <q-space />

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
          <NoDataAlert v-if="!productCatalog(filter_inactive).length" />
          <div
            v-for="(product, index) in product_list"
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
            v-if="!loading && max_shown < filtered_products.length"
            flat
            color="theme-blue"
            @click="showMore"
          >
            CARICA ALTRI
          </q-btn>
          <q-spinner v-if="loading" />
        </div>
      </div>

      <router-view />
    </q-page>
  </q-page-container>
</template>

<script>
import { mapGetters } from 'vuex';
import NoDataAlert from '@/components/NoDataAlert.vue';
import ProductCard from '@/components/ProductCard.vue';

import multiMatch from '@/lib/MultiFieldSearch.js';

export default {
  name: 'ProductList',

  components: {
    NoDataAlert,
    ProductCard,
  },

  data() {
    return {
      // search_string: null,
      loading: false,
      vuex_ready: false,
      load_quantity: 100,
      loading_round: 1,
    };
  },

  computed: {
    ...mapGetters(['productCatalog']),

    catalog() {
      return this.productCatalog(this.filter_inactive);
    },

    filtered_products() {
      return this.catalog.filter(this.match);
    },

    product_list() {
      return this.filtered_products.slice(0, this.max_shown);
    },

    max_shown() {
      return this.load_quantity * this.loading_round;
    },

    search_string: {
      get() {
        return this.$route.query.search;
      },
      set(value) {
        this.$router.replace({
          query: {
            ...this.$route.query,
            search: value,
          },
        });
      },
    },

    show_images: {
      get() {
        return this.$route.query.show_images === 'true' ? true : false;
      },
      set(value) {
        this.$router.replace({
          query: {
            ...this.$route.query,
            show_images: value,
          },
        });
      },
    },

    filter_inactive: {
      get() {
        return this.$route.query.filter_inactive === 'true' ? true : false;
      },
      set(value) {
        this.$router.replace({
          query: {
            ...this.$route.query,
            filter_inactive: value,
          },
        });
      },
    },

    card_height() {
      return this.show_images ? 240 : 150;
    },
  },

  watch: {
    search_string: {
      immediate: true,
      handler() {
        this.loading = true;
        this.loading_round = 0;
        setTimeout(() => {
          this.loading = false;
          this.loading_round = 1;
        }, 700);
      },
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
        this.$store.dispatch('loadProductList').then(() => {
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
      setTimeout(() => {
        this.loading_round++;
        this.loading = false;
      }, 700);
    },
  },
};
</script>
