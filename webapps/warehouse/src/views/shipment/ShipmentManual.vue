<template>
  <q-page
    id="shipment-root"
    class="column fit q-px-md q-py-sm"
  >
    <component :is="stageComponentMap[shipment.stage]" />
  </q-page>
</template>

<script setup>
import ShipmentConfirmation from '@/components/shipment/ShipmentConfirmation.vue';
import ShipmentInventorySelection from '@/components/shipment/ShipmentInventorySelection.vue';
import ShipmentProductsList from '@/components/shipment/ShipmentProductsList.vue';
import { useShipmentStore } from '@/stores/shipment';
import { onBeforeRouteLeave } from 'vue-router';

const shipment = useShipmentStore();

// SHIPMENT FLOW
// 1. product
// 2. inventory selection
// 2a. quantity via modal (if no serial)
// 3. confirm

const stageComponentMap = {
  product: ShipmentProductsList,
  inventory: ShipmentInventorySelection, // start position
  confirm: ShipmentConfirmation,
};

onBeforeRouteLeave(() => {
  shipment.$reset();
});
</script>
