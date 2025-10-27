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
    <q-input v-model="reason" :label="$t('movement_reason')" autogrow filled stack-label/>

    <div class="row q-col-gutter-x-sm q-mt-md">
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
import { ref } from 'vue';
import { Notify } from 'quasar';
import { sendEventsBulk } from 'app/src/composables/bulkEvent.js';
import { timestamp } from 'app/src/lib/TimeHandling';
import { useIncomingStore } from 'app/src/stores/incoming';
import PositionQuantityDistribution from 'components/PositionQuantityDistribution.vue';

const incoming = useIncomingStore();
const reason = ref('');

async function confirm() {
  let movements = [];
  const now = timestamp();

  if (incoming.product.traceability_level) {
    for (const serialCode of incoming.serials) {
      movements.push({
        position_to: incoming.positions[0]._key,
        serial_code: serialCode,
        qt_planned: 1,
        qt_confirmed: 1,
      })
    }
  }
  else {
    for (const position of incoming.positions) {
      movements.push({
        position_to: position._key,
        qt_planned: position.quantity,
        qt_confirmed: position.quantity,
      });
    }
  }

  // Build events array with just event-specific data
  const events = movements.map(movement => ({
    event_type: 'MOVEMENT_COMPLETED',
    ...movement,
    product_key: incoming.product._key,
    position_from: 'OUT',
    status: 'completed',
    movement_type: 'receipt',
    start: now,
    end: now,
    reason: reason.value,
  }));

  try {
    await sendEventsBulk(events, now);
    Notify.create({
      message: 'Movimenti registrati',
      position: 'top',
      color: 'theme-green',
      timeout: 1500,
    });
    incoming.$reset();
  } catch (err) {
    // Error already shown by sendEventsBulk
  }
}


</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
