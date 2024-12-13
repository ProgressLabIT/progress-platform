<template>
  <div class="col column full-width scroll">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto full-width">
      <div class="row">
        <div class="col">
          <div class="text-h6 q-mb-sm">PRODOTTO</div>
          <div class="text-h1 q-pr-xl" style="word-wrap: break-word">
            {{ incoming.product?.code }}
          </div>
        </div>
        <div class="col-auto">
          <div class="text-h6 text-right q-mb-sm">QUANTITÀ</div>
          <div class="text-h1 text-right">
            {{ incoming.quantity }}
          </div>
        </div>
      </div>
      <div class="text-body1 q-mt-xs">
        {{ incoming.product?.description }}
      </div>
    </div>

    <div class="text-h6 q-mb-sm q-mt-xl">DESTINAZIONE</div>
    <template v-for="position in incoming.positions" :key="position._key">
      <div class="col-auto text-h2">
        {{ position.code }}
      </div>
      <div class="row justify-center items-start content-left">
        <q-slider
          v-model="position.quantity"
          class="q-mt-lg col-10"
          :min="0"
          :max="incoming.quantity"
          :step="1"
          label
          :label-value="value"
          label-always
          :disable="position.locked"
          @change="adjust(position)"
        />
        <q-space></q-space>
        <q-btn
          color="primary"
          :icon="
            position.locked
              ? 'mdi-lock-outline'
              : 'mdi-lock-open-variant-outline'
          "
          class="col-1"
          @click="position.locked = !position.locked"
        />
      </div>
    </template>

    <q-space></q-space>

    <div class="row q-gutter-y-md">
      <q-btn
        color="theme-blue"
        label="CONFERMA"
        class="col-12"
        size="xl"
        @click="confirm"
      />
      <q-btn
        color="theme-grey"
        label="INDIETRO"
        class="col-12"
        size="xl"
        @click="incoming.stage = 'position'"
      />
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
  const session_data = store.state.session;
  for (const position of incoming.positions) {
    movements.push({
      position_from: 'Position/OUT',
      position_to: `Position/${position._key}`,
      product_key: incoming.product._key,
      qt_planned: position.quantity,
      qt_confirmed: position.quantity,
      status: 'completed',
      type: 'receipt',
      user_key: session_data.user._key,
      start: timestamp(),
      end: timestamp(),
    });
  }
  for (const movement of movements) {
    sendEvent({
      event_type: 'ADD_MOVEMENT',
      event_data: {
        movement: movement,
      },
    })
      .then(() => {
        Notify.create({
          message: 'Movimenti registrati',
          color: 'theme-green',
          timeout: 1500,
        });
      })
      .catch((err) => {
        Notify.create({
          message: err,
          color: 'theme-orange',
        });
      });
  }
  incoming.$reset();
}

function adjust(position) {
  let quantity_to_adjust = incoming.quantity;
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
