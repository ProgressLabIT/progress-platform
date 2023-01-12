<template>
  <q-page-container class="q-pa-md" style="height: 100vh">
    <q-page class="fit column">
      <!-- Header row with product filter and view controls -->
      <div class="col-auto q-py-md row q-col-gutter-lg items-center">
        <div class="col-12 col-sm-5 col-md-3">
          <q-input
            dense
            hide-bottom-space
            autocomplete="off"
            name="search"
            :placeholder="$t('search')"
            input-class="text-uppercase text-body1"
            v-model="search_proxy"
            :debounce="300">
            <template #append>
              <q-icon name="mdi-magnify" />
            </template>
          </q-input>
        </div>

        <!-- View controls -->
        <q-checkbox
          class="col-auto text-body1 low-text"
          :label="$capitalize($t('product.filters.active_only'))"
          v-model="filter_inactive">
        </q-checkbox>
        <q-checkbox
          class="col-auto text-body1 low-text"
          :label="$capitalize($t('product.filters.show_images'))"
          v-model="show_images">
        </q-checkbox>

        <q-space />

        <div class="col-auto">
          <q-btn
            color="theme-blue"
            @click="$router.push({ name: 'newProduct' })">
            {{ $t('new') }}
          </q-btn>
        </div>
      </div>

      <!-- PRODUCT LIST -->
      <div class="col scroll flex-center" id="product-list">
        <div v-if="vuex_ready" class="row q-col-gutter-lg q-mb-md">
          <NoDataAlert v-if="!productCatalog(filter_inactive).length" />
          <div
            class="col-12 col-sm-6 col-md-3 col-xl-2"
            :style="`height: ${card_height}px`"
            v-for="(product, index) in product_list"
            :key="index">
            <ProductCard
              :key="product._key"
              :product="product"
              :show_image="show_images">
            </ProductCard>
          </div>
        </div>
        <div class="row q-my-lg justify-center">
          <q-btn
            v-if="!loading && max_shown < filtered_products.length"
            flat
            color="theme-blue"
            @click="showMore">
            CARICA ALTRI
          </q-btn>
          <q-spinner v-if="loading" />
        </div>
      </div>

    </q-page>
  </q-page-container>
</template>

<script>
import LoadingSignal from '@/components/LoadingSignal.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import ProductCard from '@/components/ProductCard.vue'

import multiMatch from '@/lib/MultiFieldSearch.js'

import { mapGetters, mapActions } from 'vuex'
import { debounce as _debounce } from 'lodash'


export default {

  name: 'ProductList',
  
  components: {
    LoadingSignal,
    NoDataAlert,
    ProductCard
  },

  data() {
    return {
      search_proxy: null,
      search_string: null,
      loading: true,
      vuex_ready: false,
      max_shown: 100
    }
  },

  computed: {
    ...mapGetters(['productCatalog']),

    catalog() {
      return this.productCatalog(this.filter_inactive)
    },

    filtered_products() {
      return this.catalog.filter(this.match)
    },

    product_list() {
      return this.filtered_products.slice(0, this.max_shown)
    },

    show_images: {
      get() {
        return this.$route.query.show_images === 'true'
          ? true
          : false
      },
      set(value) {
        this.$router.replace({ 
          query: { 
            filter_inactive: this.filter_inactive,
            show_images: value 
          }
        })
      }
    },

    filter_inactive: {
      get() {
        return this.$route.query.filter_inactive === 'true'
          ? true
          : false
      },
      set(value) {
        this.$router.replace({
          query: { 
            filter_inactive: value,
            show_images: this.show_images
          }
        })
      }
    },

    card_height() {
      return this.show_images
        ? 240
        : 140
    }
  },

  methods: {
    fetchProducts() {
      return new Promise( resolve => {
        this.loading = true
        this.$store.dispatch('loadProductList').then(() => {
          setTimeout(() => this.loading = false, 2000)
          resolve()
        })
      })
    },

    match(product) {
      return multiMatch(this.search_string, product, ['code', 'description'])
    },

    showMore() {
      this.loading = true
      setTimeout(() => {
        this.max_shown += 100
        this.loading = false
      }, 1500)
    }
  },

  created() {
    this.fetchProducts().then(() => {
      this.vuex_ready = true
    })
  },

  watch: {
    search_proxy: {
      immediate: true,
      handler() {
        this.loading = true
        this.max_shown = 0,
        setTimeout(() => {
          this.search_string = this.search_proxy
          this.loading = false
          this.max_shown = 100
        }, 1500)
      }
    }
  }
};
</script>

<style lang="sass" scoped>
</style>
