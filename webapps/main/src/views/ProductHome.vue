<template>
  <v-container fill-height fluid>
    <v-row class="fill-height mx-0">
      
      <!-- LEFT COLUMN -->
      <v-col cols="4">
        <ProductAside :product="product_data"/>
      </v-col>  
    
      <!-- PRODUCT DATA -->
      <v-col cols="8" class="pa-0 pl-3">
        <v-container>
          <v-row class="mt-n3 pr-0">
            
            <!-- PARAMETERS -->
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">Parametri</h4>
                </v-container>
              </v-card>
            </v-col>  

            <!-- DOCS -->
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">documenti</h4>
                </v-container>
              </v-card>
            </v-col>  

            <!-- KPIs -->
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">indicatori</h4>
                </v-container>
              </v-card>
            </v-col>  

            <!-- ISSUES -->
            <v-col cols="6">
              <v-card flat height="35vh"> 
                <v-container class="px-5 py-4">                  
                  <h4 class="display medium highlight">segnalazioni</h4>
                </v-container>
              </v-card>
            </v-col>  
          </v-row>  
          
          <!-- PRODUCT ACTIONS -->
          <v-row>
            <v-spacer></v-spacer>
            <v-col cols="auto">
              <v-btn :color="$theme.blue">Crea ordine</v-btn>
            </v-col>  
            <v-col cols="auto">
              <v-btn :color="$theme.blue">Crea segnalazione</v-btn>
            </v-col>  
            <v-col cols="auto">
              <v-btn :color="$theme.red">Elimina</v-btn>
            </v-col>  
          </v-row>  
        </v-container>
      </v-col>

    </v-row>  
  </v-container>
</template>

<script>
// import {api} from '@/lib/apiCall.js'
import ProductAside from '@/components/ProductAside.vue'
import { mapState, mapActions } from 'vuex'

export default {

  name: 'ProductHome',
  
  components: {
    ProductAside
  },

  data() {
    return {
    };
  },

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    ...mapState({
      product_data: state => state.product.details
    })
  },

  methods: {
    ...mapActions(['loadProductDetails'])
  },

  created() {
    this.loadProductDetails(this.product_key)
  }

};
</script>

<style lang="css" scoped>
</style>
