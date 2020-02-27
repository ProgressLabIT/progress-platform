<template>

  <v-card 
    :height="image ? '160px' : '120px'" 
    outlined 
    elevation="4" class="surface-1"
    @mouseenter="overCard = true"
    @mouseleave="overCard = false"
    @dblclick="$router.push('product/'+product._key)">
    <v-img 
      :src="image ? `/pics/products/${product._key}.jpeg` : ''" 
      class="fill" 
      :style="product.active ? '' : 'filter:grayscale(1) brightness(.5)'">
      <v-container 
        class="pa-0 d-flex flex-column" 
        style="height:100%">
      
        <!-- Title and description overlay -->
        <v-sheet 
          :color="image ? 'rgba(0,0,0,.7)' : 'transparent' " 
          class="px-2 py-0"
          @mouseenter="overDesc = true" 
          @mouseleave="overDesc = false" >      
          <v-card-title class="display highlight px-0 pt-0 pb-3 nowrap">
            {{ product.code }}
          </v-card-title>
         
          <!-- the dynamic class 'nowrap' allows to show or hide 
          the full description on hover -->
          <v-card-subtitle 
            :class="['px-0 pb-1', overDesc ? '' : 'nowrap']">
            {{ product.description }}
          </v-card-subtitle>
        </v-sheet>

        <v-spacer></v-spacer>

        <!-- ACTIONS BAR -->
        <v-expand-transition>
          <ProductActions 
            :product="product" 
            v-show="showActions" 
            @showDelete="showDelete = true"
            />
        </v-expand-transition>

      </v-container>
    </v-img>
    
    <!-- DELETE CONFIRMATION -->
    <v-overlay 
      absolute 
      opacity="1" 
      :color="$theme.surface1"
      v-if="showDelete"
      class="ma-0 pa-0"
      >
      <v-container :class="image ? 'pa-6' : 'pa-3'">
        <span>Vuoi cancellare questo prodotto?</span>
        <span class="display weight-medium">{{ product.code }}</span>
        <div class="d-flex justify-space-between mt-3">
          <v-btn dark :color="$theme.red" @click.stop="trash">DELETE</v-btn>
          <v-btn dark :color="$theme.grey" @click.stop="showDelete = false">CANCEL</v-btn>
        </div>
      </v-container>
    </v-overlay>

  </v-card>  
</template>

<script>
import ProductActions from '@/components/ProductActions'
import { mapActions } from 'vuex'

export default {

  name: 'ProductCard',
  props: ['product', 'image'],

  components: {
    ProductActions
  },

  data () {
    return {
      overCard: false,
      overDesc: false,
      showDelete: false,
    }
  },

  computed: {
    showActions() {
      return this.image ? this.overCard : true
    },
  },

  methods: {
    ...mapActions(['moveToTrash']),

    trash() {
      this.moveToTrash(this.product)
      this.$emit('delete')
    }
  }

}
</script>

<style lang="css" scoped>
</style>