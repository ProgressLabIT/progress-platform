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
  if (lists.selectedItem.type === 'serial') {
    for (let inventory of shipment.selectedInventory) {
      const movement = lists.selectedItem.movements.find(m => m.serial_code === inventory.serial_code);
      updates.push({
        ...movement,
        position_from: `Position/${inventory.path.slice(-1)[0].position_key}`,
        status: 'completed',
        qt_confirmed: 1,
      });
    }
  }
  // Quantity
  else {
    const movementComplete = lists.tempQuantity + lists.selectedItem.qt_confirmed === lists.selectedItem.qt_planned
    const splitData = shipment.selectedInventory.map(position => ({
      position_from: `Position/${position.path.slice(-1)[0].position_key}`,
      qt_confirmed: position.selected,
      serial_key: position.serial_key
    }));
    updates.push({
      ...lists.selectedItem.movements[0],
      qt_confirmed: shipment.shipmentQuantity,
      split_into: splitData,
      status: movementComplete ? 'completed' : 'started'
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
        movement: {
          ...update,
          user_key: session_data.user._key,
          start: now,
          end: update.qt_confirmed === update.qt_planned ? now : null,
        }
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
    .catch((err) => {
      Notify.create({
        position: 'top',
        timeout: 0,
        message: err,
        color: 'theme-orange',
        actions: [
          { label: 'Close', textColor: 'white', handler: () => undefined }
        ]
      });
    });
    router.push({ name: 'ShipmentList', params: { listKey: router.currentRoute.value.params.listKey }})
    lists.loadLists('shipment');
    shipment.$reset()
  }
}
</script>
