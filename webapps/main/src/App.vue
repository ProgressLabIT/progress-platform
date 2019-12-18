<template>
  <v-app>

    <AppBar/>

    <v-content class="px-6">
      <!-- <HelloWorld/> -->
      <v-row justify="start" >
        <v-col cols="12" sm="4" md="3" v-for="product in products" :key="product.id">
          <ProductCard :product="product" />
        </v-col>
      </v-row>
    </v-content>

    <AppFooter />
  </v-app>
</template>

<script>
// import HelloWorld from './components/HelloWorld';
import AppBar from './components/AppBar'
import ProductCard from './components/ProductCard'
import AppFooter from './components/AppFooter'

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
        description: 'This is a sample product card is a sample product card This is a sample product card This is a sample card This is a sample product',
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
    desc_limit: 40,
    desc_trunc: 30
  }),

  methods: {
    truncate(string, limit, len) {
      if (string.length > limit) {
        return string.substring(0,len) + "..."
      }
      else return string
    }
  }
};
</script>

<style type="text/css">
</style>
