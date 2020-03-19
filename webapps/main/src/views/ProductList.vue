<template>
  <v-container fluid class="px-6 fill scroll">

    <!-- Header row with product filter and view controls -->
    <v-row>

      <!-- Text field for product filter and search -->
      <v-col cols="12" sm="5" lg="3">
        <v-text-field
          hide-details
          single-line
          autocomplete="off"
          name="search"
          label="Filtra/Cerca prodotti"
          value="search"
          v-model="searchString"
          class="ma-0 pa-0 text-uppercase">
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
          label="Solo attivi" 
          v-model="filterInactive" 
          class="ma-0 pa-0 nowrap"/>
      </v-col>    
      <v-col cols="auto" class="d-flex align-center">
        <v-checkbox 
          :ripple="false"
          color="primary"
          hide-details
          label="Mostra immagini" 
          v-model="showImages" 
          class="ma-0 pa-0 nowrap"/>
      </v-col>  

      <v-spacer></v-spacer>

      <v-col cols="auto">
        <v-btn color="primary"
          @click="$router.push({ name: 'newProduct' })">
          Crea nuovo
        </v-btn>
      </v-col>
    </v-row>

    <!-- Product List -->
    <v-row >
      <v-col cols="12" sm="6" md="3" xl="2" 
        v-for="product in notInTrash()" 
        :key="product.code" 
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
      <v-row>
        <v-col>
          Product {{ deleteSnackbar.code }} deleted  
          <v-btn text color="primary" @click.native="deleteSnackbar.show = false; ">CONFIRM</v-btn>
          <v-btn text color="warning" @click.native="undoDelete">UNDO</v-btn>
        </v-col>
        <!-- <v-col cols="12">
          <v-progress-linear height="2" v-model="deleteSnackbar.remain" />
        </v-col> -->
      </v-row>
    </v-snackbar>

    <router-view></router-view>

  </v-container>
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

    ...mapActions(['restoreProduct']),

    match(product) {
      let activeFilter = !this.filterInactive || product.active
      let searchFilter = multiMatch(this.searchString, product, ['code', 'description'])

      return activeFilter && searchFilter
    },

    deleteNotify(product) {
      const snackbar = this.deleteSnackbar
      snackbar._key = product._key
      snackbar.code = product.code
      // snackbar.remain = 100
      snackbar.show = true
      // let countdown = setInterval(() => {
      //   if (snackbar.show) {
      //     snackbar.remain -= 1
      //   }
      //   else {
      //    clearInterval(countdown)
      //   }
      // }, 60)
    },

    undoDelete() {
      this.restoreProduct(this.deleteSnackbar._key)
      this.deleteSnackbar.show = false
    }

  },

  beforeCreate() {
    this.$store.commit("UPDATE_SCREEN_TITLE", 'Libreria prodotti')
  }
};
</script>

<style lang="css" scoped>
</style>
