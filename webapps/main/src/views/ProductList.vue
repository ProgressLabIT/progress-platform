<template>
  <v-content class="px-6">

    <!-- Header row with product filter and view controls -->
    <v-row class="">

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
      <v-col class="flex-grow-0">
        <v-checkbox
          :ripple="false"
          color="primary" 
          hide-details
          label="Active only" 
          v-model="filterInactive" 
          class="ma-0 pa-0 nowrap"/>
      </v-col>    
      <v-col class="flex-grow-0">
        <v-checkbox 
          :ripple="false"
          color="primary"
          hide-details
          label="Show pictures" 
          v-model="showImages" 
          class="ma-0 pa-0 nowrap"/>
      </v-col>  

      <v-spacer></v-spacer>

      <v-col>
        <v-btn color="primary"
          @click="$router.push('new-product')">
          new product
        </v-btn>
      </v-col>
    </v-row>

    <!-- Product List -->
    <v-row >
      <v-col cols="12" sm="6" md="3" xl="2" 
        v-for="product in products" 
        :key="product.id" 
        v-show="match(product)">
        <ProductCard :product="product" :image="showImages"/>
      </v-col>
    </v-row>
    <router-view></router-view>
  </v-content>
</template>

<script>
import ProductCard from '@/components/ProductCard'  

export default {

  name: 'ProductList',
  
  components: {
    ProductCard
  },

  data: () => ({
    products: [
      {
        id: 1,
        code: 'AAA123',
        description: 'This is a sample product card is a sample product card This is This is a sample product card is a sample product card This is a a sample product',
        active: true,
        trash: false
      },
      {
        id: 2,
        code: 'BBB123',
        description: 'This is a sample product card',
        active: true,
        trash: false
      },
      {
        id: 3,
        code: 'CCC123',
        description: 'This is a sample product card',
        active: true,
        trash: false
      },
      {
        id: 4,
        code: 'DDD123',
        description: 'This is a sample product card',
        active: true,
        trash: false
      },
      {
        id: 5,
        code: 'EEE123',
        description: 'This is a sample product card',
        active: true,
        trash: false
      },
      {
        id: 6,
        code: 'FFF123',
        description: 'This is a sample product card',
        active: true,
        trash: false
      },
    ],
    searchString: '',
    showImages: true,
  }),

  methods: {
    match(product) {
      // create the list of search terms removing duplicates
      let searchTerms = [...new Set(this.searchString.toLowerCase().split(' '))]

      // create the list of words to search in, removing duplicates
      let matchString = (product.code + ' ' + product.description).toLowerCase()
      let matchContext = [...new Set(matchString.split(' '))]

      // make sure that all search terms are included in at least one word
      let match = searchTerms.every(searchTerm => {
        let termMatch = matchContext.some(matchTerm => matchTerm.includes(searchTerm))
        return termMatch
      })

      // return true (show card) if search matches or if search box empty 
      return match || this.searchString === ''
    }
  }
};
</script>

<style lang="css" scoped>
</style>
