<template>
  <div class="col column full-width">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="row col-auto full-width">
      <div class="col">
        <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
        <div class="text-h3 q-pr-xl" style="word-wrap: break-word">
          {{ incoming.product?.code }}
        </div>
      </div>
      <div class="col-auto">
        <div class="text-h6 text-right q-mb-sm">{{ $t('total') }}</div>
        <div class="text-h3 text-right">
          {{ incoming.refQuantity }}
        </div>
      </div>
    </div>

    <div
      v-if="incoming.product.traceability_level"
      class="row col-auto q-gutter-x-sm q-mt-md"
    >
      <q-card
        v-for="serial in incoming.serials"
        :key="serial"
        flat
        class="bg-theme-green q-pa-sm highlight"
      >
        {{  serial }}
      </q-card>
    </div>

    <q-icon name="mdi-arrow-down-thin" size="lg" class="q-mt-md"/>

    <div class="row items-center justify-between q-mt-lg q-mb-md">
      <div class="text-h6">
        {{$t('destination')}}
      </div>
      <div class="text-h6">
        {{$t('quantity')}}
      </div>
    </div>

    <PositionQuantityDistribution
      :positions="incoming.positions"
      :refQuantity="incoming.refQuantity"
    />

    <q-space />
    <div class="row q-col-gutter-x-sm">
      <div class="col-6">
        <q-btn
          color="theme-grey"
          class="full-width"
          :label="$t('back')"
          @click="incoming.stage = 'position'"
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
  </div>
</template>

<script setup>
import { Notify } from 'quasar';
import { useStore } from 'vuex';
import { sendEvent } from 'app/src/composables/event.js';
import { timestamp } from 'app/src/lib/TimeHandling';
import { useIncomingStore } from 'app/src/stores/incoming';
import PositionQuantityDistribution from 'components/PositionQuantityDistribution.vue';

const store = useStore();
const incoming = useIncomingStore();


function confirm() {
  let movements = [];
  let now = timestamp()
  const session_data = store.state.session;
  if (incoming.product.traceability_level) {
    for (const serialCode of incoming.serials) {
      movements.push({
        position_to: `Position/${incoming.positions[0]._key}`,
        serial_code: serialCode,
        qt_planned: 1,
        qt_confirmed: 1,
      })
    }
  }
  else {
    for (const position of incoming.positions) {
      movements.push({
        position_to: `Position/${position._key}`,
        qt_planned: position.quantity,
        qt_confirmed: position.quantity,
      });
    }
  }
  for (const movement of movements) {
    sendEvent({
      event_type: 'ADD_MOVEMENT',
      event_data: {
        movement: {
          ...movement,
          product_key: incoming.product._key,
          position_from: 'Position/OUT',
          status: 'completed',
          type: 'receipt',
          user_key: session_data.user._key,
          start: now,
          end: now
        }
      },
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
  }
  incoming.$reset();
}


</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
