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
      class="row col-auto full-width q-gutter-x-sm q-mt-md"
    >
      <q-chip
        v-for="serial in incoming.serials"
        :key="serial"
        color="theme-green"
        class="text-white weight-bold"
      >
        {{  serial }}
      </q-chip>
    </div>

    <div class="row items-center justify-between q-mt-xl q-mb-md">
      <div class="text-h6">
        {{$t('destination')}}
      </div>
      <div class="text-h6">
        {{$t('quantity')}}
      </div>
    </div>

    <template
      v-for="position in incoming.positions"
      :key="position._key"
      >
      <div class="row items-center q-col-gutter-x-sm">

      <div class="col-auto text-h3">
        {{ position.code }}
      </div>

      <div class="col-auto" v-if="incoming.positions.length > 1">
        <q-btn
          :outline="!position.locked"
          round
          size="xs"
          color="primary"
          :icon="
              position.locked
                ? 'mdi-lock-outline'
              : 'mdi-lock-open-variant-outline'
            "
            @click="position.locked = !position.locked"
        />
      </div>
      <q-space></q-space>
      <div class="col-auto text-h3 text-right">
        {{ position.quantity }}
      </div>
    </div>


      <div class="row" v-if="incoming.positions.length > 1" >
        <q-slider
          v-model="position.quantity"
          class="q-mb-md"
          style="z-index: 1000"
          :min="0"
          :max="incoming.refQuantity"
          :step="1"
          :disable="position.locked"
          @change="adjust(position)"
        />
      </div>
    </template>

    <q-space></q-space>
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

function adjust(position) {
  let quantity_to_adjust = incoming.refQuantity;
  for (const pos of incoming.positions) {
    quantity_to_adjust -= pos.quantity;
  }

  let position_index = incoming.positions.findIndex(
    (pos) => pos._key === position._key
  );

  let next_index = position_index + 1;

  while (quantity_to_adjust !== 0) {
    if (next_index === incoming.positions.length) {
      next_index = 0;
    }
    let next_position = incoming.positions[next_index];
    if (quantity_to_adjust > 0) {
      if (!next_position.locked) {
        next_position.quantity += quantity_to_adjust;
        quantity_to_adjust = 0;
      }
      next_index += 1;
    } else {
      let adjustment = 0 - quantity_to_adjust;
      let possible_adjustment =
        next_position.quantity - adjustment >= 0
          ? adjustment
          : next_position.quantity;
      if (!next_position.locked) {
        next_position.quantity -= possible_adjustment;
        quantity_to_adjust += possible_adjustment;
      }
      next_index += 1;
    }
  }
}
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
