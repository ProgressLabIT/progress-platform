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
            v-model="search_string"
            :debounce="500">
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
      <div class="col scroll flex-center">
        <LoadingSignal v-if="!vuex_ready"/>
        <NoDataAlert v-else-if="!productCatalog().length" />
        <div v-else class="row full-height q-col-gutter-md q-mb-md">
          <div
            class="col-12 col-xs-6 col-sm-4 col-md-3 col-xl-2"
            v-for="product in filtered_products"
            :key="product._key">
            <ProductCard
              :product="product"
              :image="show_images">
            </ProductCard>
          </div>
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

export default {

  name: 'ProductList',
  
  components: {
    LoadingSignal,
    NoDataAlert,
    ProductCard
  },

  data() {
    return {
      search_string: '',
      deleteSnackbar: {
        _key: null,
        code: '',
        timeout: 6200,
        show: false,
        remain: 100,
      },
      vuex_ready: false
    }
  },

  computed: {
    ...mapGetters(['productCatalog']),

    filtered_products() {
      return this.productCatalog(this.filter_inactive).filter(p => this.match(p))
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
    }
  },

  methods: {

    match(product) {
      let activeFilter = !this.filter_inactive || product.active
      let searchFilter = multiMatch(this.search_string, product, ['code', 'description'])

      return activeFilter && searchFilter
    }

  },

  created() {
    this.$store.dispatch('loadProductList').then(() => this.vuex_ready = true)
  }
};
</script>

<style lang="css" scoped>
</style>
