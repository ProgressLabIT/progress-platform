<template>
  <q-chip
    :color="contentType[item.type].color"
    class="text-body2"
    :icon="contentType[item.type].icon"
  >
    <span
      v-if="props.showFromPosition"
      class="q-ml-xs">
      {{ props.item.path.slice(-1)[0].position_code || 'IN' }}→
    </span>
    <span v-if="props.item.type === 'serial'" class="q-mr-xs">
      {{ props.item.product_code }}
    </span>
    <span :class="{'highlight': item.type !== 'product'}">
      {{ props.item.code }}
    </span>
    <span
      v-if="props.item.type === 'product'"
      class="q-ml-xs highlight">
      {{ props.item.quantity }}x
    </span>
  </q-chip>
</template>

<script setup>
const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  showFromPosition: {
    type: Boolean,
    default: false
  }
})
const contentType = {
  product: { icon: 'mdi-apps', color: 'theme-blue' },
  serial: { icon: 'mdi-cube-scan', color: 'theme-green' },
  position: { icon: 'mdi-package-variant-closed', color: 'theme-orange' },
  fixedPosition: { icon: 'mdi-file-table-box-outline', color: 'theme-grey' }
};
</script>

<style scoped>
.highlight {
  background-color: var(--q-color-theme-grey);
}
</style>
