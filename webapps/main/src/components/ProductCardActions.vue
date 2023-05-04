<template>
  <div :style="`background-color: ${$theme.surface1}aa`">
    <div class="row q-col-gutter-sm">
      <div class="col-6">
        <q-toggle
          :toggle-indeterminate="false"
          :model-value="product.active"
          @update:model-value="toggleActive(product)"
          class="q-pa-none col-6">
          <span class="text-body2">
            {{ $capitalize(product.active ? $t('active') : $t('inactive')) }}
          </span>
          <q-tooltip
            :delay="100"
            anchor="top middle"
            self="bottom middle"
            transition-show='scale'
            transition-hide="scale"
            transition-duration="200"
            class="text-body2 bg-theme-blue">
            {{ $capitalize(product.active ? $t('deactivate') : $t('reactivate')) }}
          </q-tooltip>
        </q-toggle>
      </div>
      <div class="col-6 row items-center justify-end q-pr-xs">
        <BaseTooltipIcon
          icon="mdi-clipboard-text"
          icon_size="xs"
          :tooltip="$capitalize($t('product.actions.details'))"
          :color="$theme.blue"
          @iconClick="goToProductPage('productHome')">
        </BaseTooltipIcon>
        <BaseTooltipIcon
          icon="mdi-chevron-triple-right"
          icon_size="xs"
          :tooltip="$capitalize($t('process'))"
          :color="$theme.blue"
          @iconClick="goToProductPage('productionProcess')">
        </BaseTooltipIcon>
        <BaseTooltipIcon
          icon="mdi-clipboard-list"
          icon_size="xs"
          :tooltip="$capitalize($t('component', 2))"
          :color="$theme.blue"
          @iconClick="goToProductPage('bom')">
        </BaseTooltipIcon>
        <BaseTooltipIcon
          icon="mdi-content-copy"
          icon_size="xs"
          :tooltip="$capitalize($t('copy'))"
          :color="$theme.orange"
          @iconClick="showCopy()">
        </BaseTooltipIcon>
        <BaseTooltipIcon
          icon="mdi-delete"
          icon_size="xs"
          :tooltip="$capitalize($t('delete'))"
          :color="$theme.red"
          @iconClick="confirmDelete">
        </BaseTooltipIcon>

      </div>
    </div>
  </div>
</template>

<script>
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import { mapActions } from 'vuex'
import { api } from '@/boot/axios.js'

export default {

  name: 'ProductCardActions',
  components: {
    BaseTooltipIcon
  },

  props: ['product'],
  emits: ['showDelete'],


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
          back_to: 'productList',
          ...this.$route.query
        }
      })
    },

    showCopy() {
      const dialog_title =
      this.$q.dialog({
        title: this.$t('code') + ' ' + this.$t('new') + ' ' + this.$t('product.label'),
        prompt: {
          model: '',
          type: 'text',
          isValid: val => val.length > 0,
          cancel: true,
          persistent: true
        }
      })
      .onOk(new_code => {
        const data = {
          original_product: this.product._key,
          new_code
        }
        api.post(`product/copy`, data)
        .then( async (resp) => {
          // Load product list to include navigation state for new product
          await this.$store.dispatch('loadProductList')
          this.$router.push({
            name: 'productHome',
            params: { product_key: resp.data.detail.new_product_key },
            query: { back_to: 'productList' }
          })
        })
        .catch( err => {
          if (err.response.status = 400) {
            window.alert(err.response.data.detail.message)
          }
          else {
            window.alert("An error occurred")
          }
        })
      })
    },

    confirmDelete() {
      this.$emit('showDelete')
    },
  }
}
</script>

<style lang="css" scoped>
</style>
