<template>
  <div class="col column">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto">
      <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
      <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
        {{ lists.selectedItem.product_code }}
      </div>
      <div class="text-body2 smaller q-mt-xs">
        {{ lists.selectedItem.product_description }}
      </div>
      <div
        v-if="lists.selectedItem.references.purchase_doc"
        class="text-h6 weight-bold uppercase q-mt-xs text-low">
        {{ lists.selectedItem.references.purchase_doc }}
      </div>
    </div>

    <!-- QUANTITY -->
    <div class="col column q-my-lg">
      <QuantitySelector
        v-model="lists.tempQuantity"
        heading="Quantità da confermare"
        :max="lists.selectedItem.qt_planned - lists.selectedItem.qt_confirmed"
        soft-max
        show-buttons
        class="col"
      />
    </div>
  </div>
</template>

<script setup>
import QuantitySelector from '@/components/QuantitySelector.vue';
import { useListsStore } from 'app/src/stores/lists';
const lists = useListsStore();
</script>
