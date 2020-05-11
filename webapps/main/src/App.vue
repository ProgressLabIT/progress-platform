<template>
  <v-app style="height: 100vh">
    <AppBar @showDrawer="show_drawer = true"/> 

    <v-navigation-drawer 
      temporary 
      :color="$theme.surface1"
      app width="400"
      v-model="show_drawer">
      <v-container>
        <v-tabs vertical background-color="transparent">
          
          <v-tab :to="{ name: 'productList'}" class="display mb-2">
            Libreria prodotti
          </v-tab>
          
          <v-tab :to="{ name: 'productionOverview'}" class="display mb-2">
            Monitoraggio produzione
          </v-tab>

          <v-tab :to="{ name: 'userJobs'}" class="display">
            Sessione di lavoro
          </v-tab>
          
        </v-tabs>
      </v-container>
    </v-navigation-drawer>

    <v-content class="fill">
      <div class="flex-grow-0 fill">
        <transition name="fade">
          <!-- <keep-alive > -->
            <router-view />
          <!-- </keep-alive> -->
        </transition>
      </div>
    </v-content>
    
    <AppFooter />
    
  </v-app>
</template>

<script>
import AppBar from '@/components/AppBar'
import AppFooter from '@/components/AppFooter'

export default {
  name: 'App',

  components: {
    AppBar,
    AppFooter,
  },

  data() {
    return {
      show_drawer: false,
    }
  },


  beforeCreate() {
    // this.$store.dispatch('loadProductList')
    // document.documentElement.requestFullscreen()
  },

};
</script>

<style type="text/css" scoped>
.v-tab {
  justify-content: flex-start;
}
</style>
