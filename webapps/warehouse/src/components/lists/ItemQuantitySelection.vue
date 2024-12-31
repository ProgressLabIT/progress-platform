<template>
  <div class="col column">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto">
      <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
      <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
        {{ props.item.product_code }}
      </div>
      <div class="text-body2 smaller q-mt-xs">
        {{ props.item.product_description }}
      </div>
    </div>

    <!-- QUANTITY -->
    <div class="col column q-my-lg">
      <div class="text-h3 col-auto">{{ $t('quantity') }}</div>

      <QuantitySelector v-model="tempQuantity" show-buttons class="col"/>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import QuantitySelector from '@/components/QuantitySelector.vue';

const tempQuantity = ref(0);

const props = defineProps({
  item: {
    type: Object,
    required: true
  }
});

// onMounted(() => {
//   loadPrintTemplates();
// });
</script>
