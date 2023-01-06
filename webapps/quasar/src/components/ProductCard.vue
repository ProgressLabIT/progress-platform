<template>
  <q-card
    :style="`height: ${image ? '160px' : '120px'}`"
    square
    class="surface1 product-card"
    @mouseenter="overCard = true"
    @mouseleave="overCard = false"
    @dblclick="$router.push(to_product_route)">
    <q-img
      no-spinner
      no-native-menu
      :src="image ? `/media/product/${product._key}/image.jpg` : ''"
      class="fit"
      :style="product.active ? '' : 'filter:grayscale(1) brightness(.5)'">
    </q-img>
    <div
      class="absolute-top q-pa-sm"
      :style="`background-color: ${image ? ($q.dark.isActive ? 'rgba(0,0,0,.7)' : 'rgba(230,230,230,.8)') : 'transparent'}`"
      @mouseenter="overDesc = true"
      @mouseleave="overDesc = false" >
      <div class="text-h3 display">
        {{ product.code }}
      </div>
      <div
        class="text-uppercase low-text"
        :class="['px-0 pb-1', overDesc ? '' : 'nowrap']">
        {{ product.description }}
      </div>
    </div>
    <ProductCardActions
      class="absolute-bottom"
      :product="product"
      v-show="showActions">
    </ProductCardActions>

  </q-card>
</template>

<script>
import ProductCardActions from '@/components/ProductCardActions.vue'
import { mapActions } from 'vuex'

export default {

  name: 'ProductCard',
  props: ['product', 'image'],

  components: {
    ProductCardActions
  },

  data () {
    return {
      overCard: false,
      overDesc: false,
      showDelete: false,
      to_product_route: {
        name: 'productHome',
        params: {
          product_key: this.product._key
        },
        query: {
          back_to: 'productList'
        }
      }
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

<style lang="sass" scoped>
.product-card
  border: thin solid rgba(255, 255, 255, .12)
  & .q-img__content > div
    padding: 8px !important
</style>
