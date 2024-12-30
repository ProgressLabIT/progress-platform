<template>
  <q-page
    id="incoming-root"
    class="column fit q-px-md q-py-sm"
  >
    <component :is="stageComponentMap[incoming.stage]" />
  </q-page>
</template>

<script setup>
import ConfirmPositionsPage from '@/components/incoming/position/ConfirmPositionsPage.vue';
import PositionsPage from '@/components/incoming/position/PositionsPage.vue';
import ProductsList from '@/components/incoming/products/ProductsList.vue';
import QuantitySelectionPage from '@/components/incoming/quantity/QuantitySelectionPage.vue';
import SerialSelectionPage from '@/components/incoming/quantity/SerialSelectionPage.vue';
import { useIncomingStore } from '@/stores/incoming';
import { onBeforeRouteLeave } from 'vue-router';

const incoming = useIncomingStore();


const stageComponentMap = {
  product: ProductsList,
  quantity: QuantitySelectionPage,
  serials: SerialSelectionPage,
  position: PositionsPage,
  confirm: ConfirmPositionsPage,
};

onBeforeRouteLeave(() => {
  incoming.$reset();
});
</script>
