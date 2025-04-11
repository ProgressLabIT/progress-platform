<template>
  <SlideUpCard
    :model-value="lists.selectedItem !== undefined"
    :height="cardHeight"
    @hide="close"
  >

    <!-- ITEM SELECTION (QUANTITY / SERIALS)-->
    <template v-if="step==='selection'">
      <IncomingItemSerialsSelection v-if="lists.selectedItem.type === 'serial'" />
      <IncomingItemQuantitySelection v-else />

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
            :disable="lists.movementQuantity === 0"
            unelevated
            class="full-width"
            @click="step = 'destination'"
          />
        </div>
      </div>
    </template>

    <!-- DESTINATION -->
    <template v-else-if="step==='destination'">
      <IncomingItemPosition v-model="positionsTo" @next="() => step = 'confirm'" />
      <div class="row q-mt-md">
        <div class="col">
          <q-btn
            color="theme-grey"
            :label="$t('back')"
            unelevated
            class="full-width"
            @click="() => step = 'selection'"
          />
        </div>
        <div class="q-mx-sm"></div>
        <div class="col">
          <q-btn
            color="theme-blue"
            :label="$t('next')"
            unelevated
            class="full-width"
            @click="() => step = 'confirm'"
          />
        </div>
      </div>
    </template>

    <template v-else>
      <IncomingItemConfirmation v-model="positionsTo" />
      <q-space></q-space>
      <div class="row col-auto q-col-gutter-x-sm">
        <div class="col-6">
          <q-btn
            color="theme-grey"
            class="full-width"
            :label="$t('back')"
            @click="step = 'destination'"
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
import IncomingItemQuantitySelection from 'app/src/components/lists/IncomingItemQuantitySelection.vue';
import IncomingItemSerialsSelection from 'app/src/components/lists/IncomingItemSerialsSelection.vue';
import IncomingItemPosition from 'app/src/components/lists/IncomingItemPosition.vue';
import IncomingItemConfirmation from 'app/src/components/lists/IncomingItemConfirmation.vue';
import { printProductLabel } from 'app/src/lib/print';
import { useListsStore } from 'stores/lists';
import { useStore } from 'vuex';
import { sendEvent } from '@/composables/event';
import { timestamp } from '@/lib/TimeHandling';
import { Notify } from 'quasar';
import { useRouter } from 'vue-router';

const store = useStore();
const lists = useListsStore();
const { t: $t } = useI18n();
const router = useRouter();

const cardHeight = computed(() => {
  return window.innerHeight - 50 + 'px';
});

const close = () => {
  lists.selectedItem = undefined;
  lists.tempQuantity = 0;
};

const step = ref('selection'); // destination, confirm
const positionsTo = ref([]);

function prepareMovementUpdates() {
  // It's either a single position for 1:N serials or 1:N positions for a single product qt_confirmed
  const updates = [];
  const movementComplete = lists.selectedItem.qt_confirmed + lists.movementQuantity === lists.selectedItem.qt_planned
  // Serials
  if (lists.selectedItem.type == 'serial') {
    // If serials are provided, complete the existing movements
    if (lists.selectedItem.serialsProvided) {
      for (let serial of lists.tempSerials) {
        const movement = lists.getMovementBySerial({ serialCode: serial, productCode: lists.selectedItem.product_code})
        updates.push({
          ...movement,
          movement_key: movement._key,
          position_to: positionsTo.value[0]._key,
          qt_confirmed: 1,
          status: 'completed',
        });
      }
    }
    // If serials are not provided, split the planned movement without serial
    else {
      const splitData = lists.tempSerials.map(serial => ({
        position_to: positionsTo.value[0]._key,
        qt_confirmed: 1,
        serial_code: serial
      }));
      const referenceMovement = lists.selectedItem.movements.find(m => m.status === 'planned' && m.serial_key === null)
      updates.push({
        ...referenceMovement,
        movement_key: referenceMovement._key,
        qt_confirmed: lists.movementQuantity,
        split_into: splitData,
        status: movementComplete ? 'completed' : 'started'
      });
    }
  }
  // Quantity
  else {
    const splitData = positionsTo.value.map(position => ({
      position_to: position._key,
      qt_confirmed: position.quantity,
    }));
    const referenceMovement = lists.selectedItem.movements.find(m => m.status === 'planned' && m._key !== null)
    updates.push({
      ...referenceMovement,
      movement_key: referenceMovement._key,
      qt_confirmed: lists.movementQuantity,
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
      router.push({ name: 'IncomingList', params: { listKey: router.currentRoute.value.params.listKey }})
      lists.loadLists('receipt');
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
  }
}
</script>
