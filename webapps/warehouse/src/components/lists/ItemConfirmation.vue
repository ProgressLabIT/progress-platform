<template>
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="row col-auto">
      <div class="col-8">
        <div class="text-h6 q-mb-sm">
          {{ $t('product') }}
        </div>
        <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
          {{ selectedItem.product_code }}
        </div>
        <div class="text-body2 smaller q-mt-xs ellipsis" style="max-width: 70vw;">
          {{ selectedItem.product_description }}
        </div>
        <div
          v-if="selectedItem.references.purchase_doc"
          class="text-h6 weight-bold uppercase q-mt-xs text-low">
          {{ selectedItem.references.purchase_doc }}
        </div>
      </div>

      <div class="col column items-end">
        <div class="text-h6 q-mb-sm">{{ $t('total') }}</div>
        <div class="text-h3 q-pr-sm">
          {{ lists.movementQuantity }}
        </div>
      </div>
    </div>

    <div
      v-if="lists.itemSerials.length"
      class="row col-auto q-gutter-sm q-mt-md"
    >
      <q-badge
        v-for="serial in lists.itemSerials"
        :key="serial"
        color="theme-green"
        class="text-body2 q-py-xs q-px-sm highlight"
      >
        {{ serial.serial_code }}
      </q-badge>
    </div>

    <q-icon name="mdi-arrow-down-thin" size="lg" class="col-auto q-mt-md"/>


    <div class="row col-auto items-center justify-between q-mt-lg q-mb-md">
      <div class="text-h6">
        {{$t('destination')}}
      </div>
      <div class="text-h6">
        {{$t('quantity')}}
      </div>
    </div>

    <PositionQuantityDistribution
      :positions="selectedPositions"
      :refQuantity="lists.movementQuantity"
    />



</template>

<script setup>
import { storeToRefs } from 'pinia';
import { useListsStore } from 'stores/lists'
import PositionQuantityDistribution from 'components/PositionQuantityDistribution.vue';

const lists = useListsStore();
const { selectedItem } = storeToRefs(lists);

const selectedPositions = defineModel();
</script>

