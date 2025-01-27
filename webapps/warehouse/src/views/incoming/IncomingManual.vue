<template>
  <q-page
    id="incoming-root"
    class="column fit q-px-md q-py-sm"
  >
    <component :is="stageComponentMap[incoming.stage]" />
  </q-page>
</template>

<script setup>
import IncomingConfirmPositionsPage from '@/components/incoming/position/IncomingConfirmPositionsPage.vue';
import IncomingPositionsPage from '@/components/incoming/position/IncomingPositionsPage.vue';
import IncomingProductsList from '@/components/incoming/products/IncomingProductsList.vue';
import IncomingQuantitySelectionPage from '@/components/incoming/quantity/IncomingQuantitySelectionPage.vue';
import IncomingSerialSelectionPage from '@/components/incoming/quantity/IncomingSerialSelectionPage.vue';
import { useIncomingStore } from '@/stores/incoming';
import { onBeforeRouteLeave } from 'vue-router';

const incoming = useIncomingStore();

// RECEIPT FLOW
// 1. product
// 2a. quantity
// 2b. serials
// 3. position (destination)
// 4. confirm

const stageComponentMap = {
  product: IncomingProductsList,
  quantity: IncomingQuantitySelectionPage,
  serials: IncomingSerialSelectionPage,
  position: IncomingPositionsPage, // destination position
  confirm: IncomingConfirmPositionsPage,
};

onBeforeRouteLeave(() => {
  incoming.$reset();
});
</script>
