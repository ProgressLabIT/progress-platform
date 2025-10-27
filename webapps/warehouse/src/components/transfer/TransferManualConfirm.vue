<template>
  <div class="column col q-gutter-y-md">
    <!-- Selected Serials Section -->
    <div class="text-h6">
      {{ $t('contents') }}
      <q-chip size="sm" color="theme-grey" class="q-ml-sm">
        {{ transfer.contents.length }}
      </q-chip>
    </div>
    <q-scroll-area class="col q-mt-sm">
      <div class="row q-col-gutter-x-xs">
        <div v-for="item in transfer.contents.sort((a, b) => a.code.localeCompare(b.code))" :key="item._key" class="col-auto">
          <ContentChip :item="item" :show-from-position="transfer.selectMode === 'product'" />
        </div>
      </div>
    </q-scroll-area>

    <q-icon name="mdi-arrow-down-thin" size="lg" class="q-mt-md"/>


    <!-- Destination Position Section -->
    <div class="q-mb-md">
      <div class="text-h6">{{ $t('destination') }}</div>
      <q-chip color="theme-grey" class="text-body2 highlight q-mt-sm">
        {{ transfer.destinationPosition.code }}
      </q-chip>
    </div>

    <q-space />

    <q-input v-model="reason" :label="$t('movement_reason')" autogrow filled stack-label/>

    <!-- Action Buttons -->
    <div class="row q-col-gutter-sm col-auto">
      <div class="col-6">
        <q-btn
          color="grey"
          :label="$t('back')"
          class="full-width"
          @click="transfer.stage = 'destination'"
        />
      </div>
      <div class="col-6">
        <q-btn
          color="primary"
          :label="$t('confirm')"
          class="full-width"
          @click="saveTransfer"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { Notify } from 'quasar';
import { useTransferStore } from '@/stores/transfer';
import { sendEventsBulk } from 'app/src/composables/bulkEvent.js';
import { timestamp } from 'app/src/lib/TimeHandling';
import ContentChip from '../ContentChip.vue';

const transfer = useTransferStore();
const reason = ref('');
async function saveTransfer() {
  let movements = [];
  const now = timestamp();

  for (const item of transfer.contents) {
    const position_from_key = item.type === 'position' ? item.position_key : (transfer.startPosition?._key ?? item.path.slice(-1)[0].position_key);
    if (position_from_key === null) {
      Notify.create({
        message: 'Errore: movimenti con posizione di origine non disponibile',
        position: 'top',
        color: 'theme-red',
      });
      return;
    }
    movements.push({
      position_from: position_from_key,
      position_to: transfer.destinationPosition._key,
      product_key: item.type === 'position' ? null : item.product_key,
      serial_key: item.type === 'serial' ? item.serial_key : null,
      qt_planned: item.type === 'product' ? item.quantity : 1,
      qt_confirmed: item.type === 'product' ? item.quantity : 1,
      status: 'completed',
      movement_type: 'transfer',
      start: now,
      end: now,
      reason: reason.value,
    });
  }

  // Build events array with just event-specific data
  const events = movements.map(movement => ({
    event_type: 'MOVEMENT_COMPLETED',
    ...movement,
  }));

  try {
    await sendEventsBulk(events, now);
    Notify.create({
      message: 'Movimenti registrati',
      position: 'top',
      color: 'theme-green',
      timeout: 1500,
    });
    transfer.$reset();
  } catch (err) {
    // Error already shown by sendEventsBulk
  }
}
</script>
