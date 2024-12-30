<template>
  <div class="column col q-gutter-y-md">
    <!-- Selected Serials Section -->
    <div class="text-h6">
      {{ $t('contents') }}
      <q-chip size="sm" color="theme-grey" class="q-ml-sm">
        {{ transfer.contents.length }}
      </q-chip>
    </div>
    <div class="row q-col-gutter-x-xs q-mt-sm">
      <!-- Show first 3 serial numbers as chips -->
      <div v-for="item in transfer.contents" :key="item._key" class="col-auto">
        <q-chip color="theme-grey" class="text-body2" :icon="contentIcon[item.type]">
          <span>{{ item.code }}</span>
          <span v-if="item.type === 'product'">x {{ item.quantity }}</span>
        </q-chip>
      </div>
      <!-- Show count of remaining serials if more than 3 are selected -->
      <!-- <div v-if="transfer.contents.length > 3" class="col-auto">
        <q-chip color="theme-grey" class="text-body2">
          +{{ transfer.contents.length - 3 }}
        </q-chip>
      </div> -->
    </div>


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

const contentIcon = {
  product: 'mdi-apps',
  serial: 'mdi-cube-scan',
  position: 'mdi-package-variant-closed',
}

function saveTransfer() {
  transfer.selectMode === 'serials'
  ? confirmSerialMovements()
  : confirmProductMovements();
}

function confirmSerialMovements() {
  let movements = [];
  const session_data = store.state.session;

  for (const serial of transfer.contents) {
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
  transfer.contents.forEach(s => serial_keys.append('serial_keys', s._key));
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

function getProductKey(item) {
  switch(item.type) {
    case 'product': return item._key;
    case 'serial': return item.product_key;
    case 'position': return null;
  }
}

function confirmProductMovements() {
  let movements = [];
  const now = timestamp()
  const session_data = store.state.session;

  for (const item of transfer.contents) {
    movements.push({
      position_from: `Position/${item.type === 'position' ? item._key : transfer.startPosition._key}`,
      position_to: `Position/${transfer.destinationPosition._key}`,
      product_key: getProductKey(item),
      serial_key: item.type === 'serial' ? item._key : null,
      quantity: item.type === 'product' ? item.quantity : 1,
      status: 'completed',
      type: 'transfer',
      user_key: session_data.user._key,
      start: now,
      end: now,
    });
  }

  for (const movement of movements) {
    sendEvent({
      event_type: 'ADD_MOVEMENT',
      event_data: {movement},
    })
    .then(() => {
      Notify.create({
        message: 'Movimenti registrati',
        position: 'top',
        color: 'theme-green',
        timeout: 1500,
      });
      transfer.$reset();
    })
    .catch(err => {
      Notify.create({
        message: err,
        position: 'top',
        color: 'theme-orange',
        timeout: 0,
        actions: [
          {
            label: 'Close', color: 'white', handler: () => undefined
          }
        ]

      })
    });
  }
}

</script>
