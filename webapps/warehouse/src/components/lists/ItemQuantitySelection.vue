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
      <div class="text-h3 col-auto">Quantità da confermare</div>

      <QuantitySelector
        v-model="lists.tempQuantity"
        show-buttons
        class="col"
        :max="selectedItem.qt_planned - selectedItem.qt_confirmed"
      />
    </div>
  </div>
</template>

<script setup>
import QuantitySelector from '@/components/QuantitySelector.vue';
import { useListsStore } from 'app/src/stores/lists';
import { storeToRefs } from 'pinia';
const lists = useListsStore();
const { selectedItem } = storeToRefs(lists);
</script>
