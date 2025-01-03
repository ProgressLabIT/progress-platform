<template>
  <SlideUpCard
    :model-value="lists.selectedItem !== undefined"
    height="95vh"
    @hide="close"
  >

    <!-- ITEM SELECTION (QUANTITY / SERIALS)-->
    <template v-if="step==='selection'">
      <ItemSerialsSelection v-if="lists.selectedItem.type === 'serial'" />
      <ItemQuantitySelection v-else />

      <q-btn
        color="theme-blue"
        :label="$t('print_label')"
        unelevated
        class="full-width"
        @click="printProductLabel(lists.selectedItem.product_code, lists.selectedItem.product_description)"
      />
      <q-btn
        color="theme-blue"
        :label="$t('next')"
        :disable="lists.selectedItem.qt_confirmed === 0"
        unelevated
        class="full-width q-mt-md"
        @click="step = 'destination'"
      />
    </template>

    <!-- DESTINATION -->
    <template v-else-if="step==='destination'">
      <ItemPosition v-model="positionsTo" @next="() => step = 'confirm'" />
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
      <ItemConfirmation v-model="positionsTo" />
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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import SlideUpCard from 'app/src/components/SlideUpCard.vue';
import ItemQuantitySelection from 'app/src/components/lists/ItemQuantitySelection.vue';
import ItemSerialsSelection from 'app/src/components/lists/ItemSerialsSelection.vue';
import ItemPosition from 'app/src/components/lists/ItemPosition.vue';
import ItemConfirmation from 'app/src/components/lists/ItemConfirmation.vue';
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

const close = () => {
  lists.selectedItem = undefined;
};

const step = ref('selection'); // destination, confirm
const positionsTo = ref([]);

function prepareMovementUpdates() {
  // It's either a single position for 1:N serials or 1:N positions for a single product qt_confirmed
  const updates = [];

  // Serials
  if (lists.selectedItem.type == 'serial') {
    for (let movement of lists.selectedItem.movements.filter(m => m.qt_confirmed === 1)) {
      updates.push({
        ...movement,
        position_to: `Position/${positionsTo.value[0]._key}`,
        status: 'completed',
      });
    }
  }
  // Products with one destination
  else if (positionsTo.value.length === 1) {
    console.log('quantity single')
    updates.push({
      ...lists.selectedItem.movements[0],
      position_to: `Position/${positionsTo.value[0]._key}`,
      status: 'completed',
    });
  }
  // Products with multiple destinations
  else {
    console.log('quantity multiple')
    const splitData = positionsTo.value.map(position => ({
      position_to: `Position/${position._key}`,
      qt_confirmed: position.quantity,
    }));
    updates.push({
      ...lists.selectedItem.movements[0],
      qt_confirmed: lists.selectedItem.qt_confirmed,
      split_into: splitData,
      status: 'completed',
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
          end: now,
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
      lists.loadLists('receipt');
      router.push({ name: 'IncomingList', params: { listKey: lists.selectedItem.list_key }})
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
