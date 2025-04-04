<template>
  <div class="col column full-width">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="row col-auto full-width">
      <div class="col">
        <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
        <div class="text-h3 q-pr-xl" style="word-wrap: break-word">
          {{ lists.selectedItem?.product_code }}
        </div>
      </div>
      <div class="col-auto">
        <div class="text-h6 text-right q-mb-sm">{{ $t('total') }}</div>
        <div class="text-h3 text-right">
          {{ shipment.shipmentQuantity }} / {{ lists.selectedItem.qt_planned }}
        </div>
      </div>
    </div>


    <!-- Source positions and quantities/serials -->
    <div class="row items-center justify-between q-mt-lg q-mb-md">
      <div class="text-h6">
        Origine
      </div>
      <div class="text-h6">
        {{ sendingSerials ? 'Seriale' : $t('quantity') }}
      </div>
    </div>

     <q-scroll-area class="col full-width">

      <!-- Contents -->
      <template v-for="item in shipment.selectedInventory" :key="item._key">
        <div class="row items-center q-col-gutter-x-sm q-mt-sm">
          <div class="col text-h4">
            {{ item.path.slice(-1)[0].position_code }}
          </div>
          <div class="col-auto">
            <q-card
              v-if="sendingSerials"
              flat
              class="bg-theme-green q-pa-sm highlight"
            >
              {{ item.serial_code }}
            </q-card>
            <div v-else class="col-auto text-h3 text-right">
              {{ item.selected }}
            </div>
          </div>
        </div>
      </template>

    </q-scroll-area>


    <q-icon name="mdi-arrow-down-thin" size="lg" class="q-mt-md"/>

    <div class="text-h3 q-mt-md q-mb-xl">
      OUT
    </div>

    <q-space></q-space>

  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useShipmentStore } from '@/stores/shipment';
import { useListsStore } from '@/stores/lists';

const shipment = useShipmentStore();
const lists = useListsStore();


const sendingSerials = computed(() => {
  return shipment.inventory[0].serial_key != null
});
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
