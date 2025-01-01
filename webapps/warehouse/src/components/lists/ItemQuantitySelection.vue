<template>
  <div class="col column">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto">
      <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
      <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
        {{ movement.product_code }}
      </div>
      <div class="text-body2 smaller q-mt-xs">
        {{ movement.product_description }}
      </div>
    </div>

    <!-- QUANTITY -->
    <div class="col column q-my-lg">
      <div class="text-h3 col-auto">{{ $t('quantity') }}</div>

      <QuantitySelector
        v-model="movement.qt_confirmed"
        show-buttons
        class="col"
        :max="movement.qt_planned"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import QuantitySelector from '@/components/QuantitySelector.vue';
import { useListsStore } from 'app/src/stores/lists';

const lists = useListsStore()

const movement = computed(() => lists.getMovementByKey(lists.selectedItem.movements[0]._key))
</script>
