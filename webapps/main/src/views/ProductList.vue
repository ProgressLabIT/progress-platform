<template>
  <v-content class="px-6">

    <!-- Header row with product filter and view controls -->
    <v-row>

      <!-- Text field for product filter and search -->
      <v-col cols="12" sm="5" lg="3">
        <v-text-field
          hide-details
          single-line
          autocomplete="false"
          name="search"
          label="PRODUCTS FILTER/SEARCH"
          value="search"
          v-model="searchString"
          class="ma-0 pa-0">
          <template v-slot:append>
            <span class="material-icons">search</span>
          </template>
        </v-text-field>
      </v-col>

      <!-- View controls -->
      <v-col cols="auto" class="d-flex align-center">
        <v-checkbox
          :ripple="false"
          color="primary" 
          hide-details
          label="Active only" 
          v-model="filterInactive" 
          class="ma-0 pa-0 nowrap"/>
      </v-col>    
      <v-col cols="auto" class="d-flex align-center">
        <v-checkbox 
          :ripple="false"
          color="primary"
          hide-details
          label="Show pictures" 
          v-model="showImages" 
          class="ma-0 pa-0 nowrap"/>
      </v-col>  

      <v-spacer></v-spacer>

      <v-col cols="auto">
        <v-btn color="primary"
          @click="$router.push('product/new-product')">
          new product
        </v-btn>
      </v-col>
    </v-row>

    <!-- Product List -->
    <v-row >
      <v-col cols="12" sm="6" md="3" xl="2" 
        v-for="product in notInTrash()" 
        :key="product._key" 
        v-show="(!filterInactive || product.active) && match(product)">
        <ProductCard 
          :product="product" 
          :image="showImages" 
          @delete="deleteNotify(product)"
          />
      </v-col>
    </v-row>


    <!-- DELETE/RESTORE NOTIFICATION -->
    <v-snackbar id="delete-notification" bottom left 
      v-model="deleteSnackbar.show" 
      :timeout="deleteSnackbar.timeout">
      <v-row column wrap>
        <v-col>
          Product {{ deleteSnackbar.code }} deleted  
          <v-btn text color="primary" @click.native="deleteSnackbar.show = false; ">CONFIRM</v-btn>
          <v-btn text color="warning" @click.native="undoDelete">UNDO</v-btn>
        </v-col>
        <v-col>
          <v-progress-linear height="2" v-model="deleteSnackbar.remain" />
        </v-col>
      </v-row>
    </v-snackbar>

    <!-- Product Modals entry point -->
    <router-view :links="['home', 'process', 'bom', 'docs']" title="Product ID:"></router-view>

  </v-content>
</template>

<script>
import ProductCard from '@/components/ProductCard' 
import multiMatch from '@/lib/MultiFieldSearch.js'

import { mapGetters, mapActions } from 'vuex'

export default {

  name: 'ProductList',
  
  components: {
    ProductCard
  },

  data: () => ({
    filterInactive: false,
    searchString: '',
    showImages: false,
    deleteSnackbar: {
      _key: null,
      code: '',
      timeout: 6200,
      show: false,
      remain: 100,
    }
  }),

  computed: {
    ...mapGetters(['notInTrash']),
  },

  methods: {

    ...mapActions(['restoreProduct', 'loadProductList']),

    match(product) {
      let activeFilter = !this.filterInactive || product.active
      let searchFilter = multiMatch(this.searchString, product, ['code', 'description'])

      return activeFilter && searchFilter
    },

    deleteNotify(product) {
      const snackbar = this.deleteSnackbar
      snackbar._key = product._key
      snackbar.code = product.code
      snackbar.remain = 100
      snackbar.show = true
      let countdown = setInterval(() => {
        if (snackbar.show) {
          snackbar.remain -= 1
        }
        else {
         clearInterval(countdown)
        }
      }, 60)
    },

    undoDelete() {
      this.restoreProduct(this.deleteSnackbar._key)
      this.deleteSnackbar.show = false
    }

  },

  created() {
    // console.log("Loading products...")
    this.loadProductList()
  }
};
</script>

<style lang="css" scoped>
</style>
