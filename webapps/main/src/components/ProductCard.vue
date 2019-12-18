<template>

  <v-card height="160px" outlined elevation="4" class="surface-1"
    @mouseover="overCard = true"
    @mouseleave="overCard = false">
    <v-img :src="`pics/products/${product.id}.jpeg`" class="fill">
      <v-container class="pa-0 d-flex flex-column" style="height:100%">
        <!-- <v-row class="pa-0"> -->
          <!-- <v-col class="pa-0"> -->
      
        <v-sheet 
          color="rgba(0,0,0,.7)" 
          class="px-2 py-0"
          @mouseover="overDesc = true" 
          @mouseleave="overDesc = false" >      
          <v-card-title class="display highlight px-0 pt-0 pb-3">
            {{ product.code }}
          </v-card-title>
         
          <!-- the dynamic class truncate-text allows to show or hide 
          the full description on hover -->
          <v-card-subtitle 
            :class="['px-0 pb-1', overDesc ? '' : 'truncate-text']">
            {{ product.description }}
          </v-card-subtitle>
        </v-sheet>
        <v-spacer></v-spacer>
        <v-expand-transition>
          <ProductActions :product="product" v-show="overCard"/>
        </v-expand-transition>
      </v-container>
    </v-img>
  </v-card>  
</template>

<script>
import ProductActions from '@/components/ProductActions'

export default {

  name: 'ProductCard',
  props: ['product'],

  components: {
    ProductActions
  },

  data () {
    return {
      overCard: false,
      overDesc: false,
    }
  }

}
</script>

<style lang="css" scoped>
</style>