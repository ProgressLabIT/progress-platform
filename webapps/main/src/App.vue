<template>
  <v-app>
    <AppBar/>    
      <router-view />
    <AppFooter />
  </v-app>
</template>

<script>
// import HelloWorld from './components/HelloWorld';
import AppBar from '@/components/AppBar'
import AppFooter from '@/components/AppFooter'

export default {
  name: 'App',

  components: {
    AppBar,
    AppFooter,
  },

  created() {
    this.$store.dispatch('loadProductList')
    // document.documentElement.requestFullscreen()
  }

};
</script>

<style type="text/css">
</style>
