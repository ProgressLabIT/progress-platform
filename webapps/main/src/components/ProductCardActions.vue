<template>
  <v-sheet class="surface-1">
    <v-row class="pa-0">

      <!-- ACTIVE TOGGLE -->
      <v-col cols="6" class="py-0">        
        <v-tooltip top 
          color="primary"
          open-delay="300">
          <template v-slot:activator="{on}">
            
            <v-switch 
              flat hide-details
              color="primary"
              :input-value="product.active"
              v-on="on"
              @change="toggleActive(product)"
              class="pa-2 ma-0">
              <template v-slot:label>
                <span class="body-2 text-truncate">
                  {{ product.active ? $tc('active') : $tc('inactive') | capitalize }}
                </span>
              </template>
            </v-switch>
          </template>
          <span class="no-transition">
            {{ product.active ? $tc('deactivate') : $tc('reactivate') | capitalize }}
          </span>
        </v-tooltip>
      </v-col>

      <v-spacer></v-spacer>

      <!-- OPTIONS -->
      <v-col cols="6" class="d-flex py-0 align-center justify-end">
        <BaseTooltipIcon
          icon="assignment"
          :tooltip="$tc('product.actions.details') | capitalize"
          :color="$theme.blue"
          @iconClick="goToProductPage('productHome')"/>
        <BaseTooltipIcon
          icon="mdi-chevron-triple-right"
          :tooltip="$tc('process') | capitalize"   
          :color="$theme.blue"
          @iconClick="goToProductPage('productionProcess')"/>
        <BaseTooltipIcon
          icon="mdi-clipboard-list"
          :tooltip="$tc('component', 2) | capitalize"
          :color="$theme.blue"
          @iconClick="goToProductPage('bom')"/>
        <BaseTooltipIcon
          icon="delete"
          :tooltip="$tc('delete') | capitalize"
          :color="$theme.red"
          @iconClick="confirmDelete"
          />
      </v-col>
    </v-row>
  </v-sheet>
</template>

<script>
import BaseTooltipIcon from '@/components/BaseTooltipIcon'
import { mapActions } from 'vuex'
export default {

  name: 'ProductCardActions',
  components: {
    BaseTooltipIcon
  },

  props: ['product'],
  data () {
    return {
      // overSwitch: false
    }
  },

  methods: {
    ...mapActions(['switchActiveState']),

    toggleActive(product) {
      this.switchActiveState(product)
    },

    goToProductPage(page) {
      this.$router.push({
        name: page,
        params: {
          product_key: this.product._key
        },
        query: {
          back_to: 'productList'
        }
      })
    },

    confirmDelete() {
      this.$emit('showDelete')
    }
  }
}
</script>

<style lang="css" scoped>
</style>