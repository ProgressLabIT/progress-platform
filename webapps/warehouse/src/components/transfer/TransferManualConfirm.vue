<template>
  <div class="column col">
    <!-- Selected Serials Section -->
    <template v-if="transfer.selectMode === 'serials'">
      <div class="q-mb-md">
        <div class="text-h6">
          {{ $t('serial', 2) }}
          <q-avatar size="sm" color="theme-grey" class="q-ml-sm">
          {{ transfer.contents.serials.length }}
        </q-avatar>
      </div>
      <div class="row q-col-gutter-x-xs q-mt-sm">
        <div v-for="serial in transfer.contents.serials" :key="serial._key" class="col-auto">
          <q-chip color="theme-grey" class="text-body2 highlight">
            {{ serial.code }}
          </q-chip>
        </div>
      </div>
    </div>
    </template>

    <!-- Destination Position Section -->
    <div class="q-mb-md">
      <div class="text-h6">{{ $t('destination') }}</div>
      <q-chip color="theme-grey" class="text-body2 highlight q-mt-sm">
        {{ transfer.destinationPosition.code }}
      </q-chip>
    </div>

    <q-space />

    <!-- Action Buttons -->
    <div class="row q-col-gutter-sm">
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
import { Notify } from 'quasar';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import { useTransferStore } from '@/stores/transfer';
import { sendEvent } from 'app/src/composables/event.js';
import { timestamp } from 'app/src/lib/TimeHandling';

const transfer = useTransferStore();
const store = useStore();

function saveTransfer() {
  transfer.selectMode === 'serials'
  ? confirmSerialMovements()
  : confirmProductMovements();
}

function confirmSerialMovements() {
  let movements = [];
  const session_data = store.state.session;

  for (const serial of transfer.contents.serials) {
    movements.push({
      position_to: `Position/${transfer.destinationPosition._key}`,
      product_key: serial.product._key,
      serial_key: serial._key,
      qt_planned: 1,
      qt_confirmed: 1,
      status: 'completed',
      type: 'transfer',
      user_key: session_data.user._key,
      start: timestamp(),
      end: timestamp(),
    });
  }

  const serial_keys = new URLSearchParams();
  transfer.contents.serials.forEach(s => serial_keys.append('serial_keys', s._key));
  const promises = [];
  api
    .get('/inventory', { params: serial_keys })
    .then(({ data }) => {
      for (const movement of movements) {
        // this works only for serials. TODO: add products/positions
        movement.position_from = `Position/${data.find(s => s.serial_key === movement.serial_key).position_key}`;
        promises.push(sendEvent({
          event_type: 'ADD_MOVEMENT',
          event_data: {movement},
        }))
      }
      Promise.all(promises)
      .then(() => {
        Notify.create({
          message: 'Movimenti registrati',
          position: 'top',
          color: 'theme-green',
          timeout: 1500,
        });
      })
      .catch(err => {
        console.log(err);
      });
    })
    .catch(err => {
      console.log(err);
    });

  console.log(movements);
  transfer.$reset();
}

function confirmProductMovements() {
  console.log('confirmProductMovements');
}

</script>
