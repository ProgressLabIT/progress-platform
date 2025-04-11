<template>
  <SlideUpCard
    :model-value="lists.selectedItem !== undefined"
    :height="cardHeight"
    @hide="close"
  >

    <!-- ITEM SELECTION (QUANTITY / SERIALS)-->
    <template v-if="step==='selection'">
      <ShipmentItemInventorySelection />

      <div class="row q-mt-md q-gutter-x-sm">
        <div class="col">
          <q-btn
            color="theme-blue"
            label="etichetta"
            unelevated
            class="full-width"
            @click="printProductLabel(lists.selectedItem.product_code, lists.selectedItem.product_description)"
          />
        </div>
        <div class="col">
          <q-btn
            color="theme-blue"
            :label="$t('next')"
            :disable="shipment.shipmentQuantity === 0"
            unelevated
            class="full-width"
            @click="step = 'destination'"
          />
        </div>
      </div>
    </template>


    <template v-else>
      <ShipmentItemConfirmation v-model="positionsTo" />
      <q-space></q-space>
      <div class="row col-auto q-col-gutter-x-sm">
        <div class="col-6">
          <q-btn
            color="theme-grey"
            class="full-width"
            :label="$t('back')"
            @click="step = 'selection'"
          />
        </div>
        <div class="col-6">
          <q-btn
            color="theme-blue"
            class="full-width"
            :label="$t('confirm')"
            @click="confirm"
          />
        </div>
      </div>
    </template>


  </SlideUpCard>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import SlideUpCard from 'app/src/components/SlideUpCard.vue';
import { printProductLabel } from 'app/src/lib/print';
import { useListsStore } from 'stores/lists';
import { useShipmentStore } from 'stores/shipment';
import { useStore } from 'vuex';
import { sendEvent } from '@/composables/event';
import { timestamp } from '@/lib/TimeHandling';
import { Notify } from 'quasar';
import { useRouter } from 'vue-router';
import ShipmentItemInventorySelection from '@/components/lists/ShipmentItemInventorySelection.vue';
import ShipmentItemConfirmation from '@/components/lists/ShipmentItemConfirmation.vue';

const store = useStore();
const lists = useListsStore();
const { t: $t } = useI18n();
const router = useRouter();
const shipment = useShipmentStore();
const cardHeight = computed(() => {
  return window.innerHeight - 50 + 'px';
});

const close = () => {
  lists.selectedItem = undefined;
  lists.tempQuantity = 0;
  shipment.$reset()
};

const step = ref('selection'); // destination, confirm
const positionsTo = ref([]);

function prepareMovementUpdates() {
  // It's either a single position for 1:N serials or 1:N positions for a single product qt_confirmed
  const updates = [];
  // Serials
  if (lists.selectedItem.type === 'serial' && lists.selectedItem.serialsProvided) {
    // Planned movements may have no serial code. If there are planned movement with the serial code provided, use it.
    for (let inventory of shipment.selectedInventory) {
      const movement = lists.selectedItem.movements.find(m => m.serial_code === inventory.serial_code);
      updates.push({
        ...movement,
        movement_key: movement._key,
        position_from: inventory.path.slice(-1)[0].position_key,
        status: 'completed',
        qt_confirmed: 1,
      });
    }
  }
  // Movements with no traceability or without specified serial codes
  else {
    const splitData = shipment.selectedInventory.map(inventory => ({
      position_from: inventory.path.slice(-1)[0].position_key,
      qt_confirmed: inventory.selected,
      serial_key: inventory.serial_key
    }));
    // Find the planned movement to use as reference
    const referenceMovement = lists.selectedItem.movements.find(m => m.status === 'planned')
    updates.push({
      ...referenceMovement,
      movement_key: referenceMovement._key,
      qt_confirmed: shipment.shipmentQuantity,
      split_into: splitData,
    });
  }
  return updates
}

function confirm() {
  // Send events
  let now = timestamp()
  const session_data = store.state.session;

  for (const update of prepareMovementUpdates()) {
    sendEvent({
      event_type: 'MOVEMENT_UPDATED',
      timestamp: now,
      event_data: {
        user_key: session_data.user._key,
        ...update,
        start: now,
        end: update.qt_confirmed === update.qt_planned ? now : null,
      }
    })
    .then(() => {
      Notify.create({
        message: 'Movimenti registrati',
        position: 'top',
        color: 'theme-green',
        timeout: 1500,
      });
    })
    router.push({ name: 'ShipmentList', params: { listKey: router.currentRoute.value.params.listKey }})
    lists.loadLists('shipment');
    shipment.$reset()
  }
}
</script>
