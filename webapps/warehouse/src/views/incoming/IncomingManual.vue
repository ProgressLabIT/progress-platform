<template>
  <q-page
    id="incoming-root"
    class="q-px-md q-pt-lg column fit q-col-gutter-y-lg"
  >
    <!-- TITLE -->
    <div class="text-h3 uppercase col-auto text-primary">Nuovo Ricevimento</div>
    <component :is="stageComponentMap[incoming.stage]" />
  </q-page>
</template>

<script setup>
import ConfirmPositionsPage from '@/components/incoming/position/ConfirmPositionsPage.vue';
import PositionsPage from '@/components/incoming/position/PositionsPage.vue';
import ProductsList from '@/components/incoming/products/ProductsList.vue';
import QuantitySelectionPage from '@/components/incoming/quantity/QuantitySelectionPage.vue';
import { useIncomingStore } from '@/stores/incoming';
const incoming = useIncomingStore();


const stageComponentMap = {
  product: ProductsList,
  quantity: QuantitySelectionPage,
  position: PositionsPage,
  confirm: ConfirmPositionsPage,
};
</script>
