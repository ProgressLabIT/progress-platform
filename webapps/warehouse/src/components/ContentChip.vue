<template>
  <q-chip color="theme-grey" class="text-body2 highlight" :icon="contentIcon[item.type]">
    <span>{{ props.item.code }}</span>
    <span v-if="props.item.type === 'product'" class="q-ml-xs">{{ props.item.quantity }}x</span>
  </q-chip>
</template>

<script setup>
const props = defineProps({
  item: {
    type: Object,
    required: true
  }
})
const contentIcon = {
  product: 'mdi-apps',
  serial: 'mdi-cube-scan',
  position: 'mdi-package-variant-closed',
};
</script>
