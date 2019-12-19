<template>
  <v-app>

    <AppBar/>

    <v-content class="px-6">
      <!-- <HelloWorld/> -->
      <v-row class="py-0">
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
        <v-spacer></v-spacer>
        <v-col class="flex-grow-0">
          <v-checkbox
            color="primary" 
            hide-details
            label="Active only" 
            v-model="filterInactive" 
            value="false"
            class="ma-0 pa-0 nowrap"/>
        </v-col>    
        <v-col class="flex-grow-0">
          <v-checkbox 
            color="primary"
            hide-details
            label="Show pictures" 
            v-model="showImages" 
            value="false"
            class="ma-0 pa-0 nowrap"/>
        </v-col>  
      </v-row>
      <v-row >
        <v-col cols="12" sm="4" md="3" xl="2" 
          v-for="product in products" 
          :key="product.id" 
          v-show="match(product)">
          <ProductCard :product="product" :image="showImages"/>
        </v-col>
      </v-row>
    </v-content>

    <AppFooter />
  </v-app>
</template>

<script>
// import HelloWorld from './components/HelloWorld';
import AppBar from '@/components/AppBar'
import ProductCard from '@/components/ProductCard'
import AppFooter from '@/components/AppFooter'

export default {
  name: 'App',

  components: {
    AppBar,
    ProductCard,
    AppFooter,
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
    showImages: false,
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

<style type="text/css">
</style>
