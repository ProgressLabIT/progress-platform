<template>
  <q-page class="q-px-md q-pb-md q-py-sm column fit">


    <div class="row justify-between">
      <div class="col-auto">
        <div class="text-h5 text-low">
          {{ list?.references?.partner_name }}
        </div>
        <div class="text-h3">{{ list?.code }}</div>
      </div>
      <div class="col-auto">
        <div class="text-h5 text-low">
          Da controllare
        </div>
        <div class="text-right text-body1">
          {{ listItems?.filter(i => i.status !== 'completed').length }} / {{  listItems?.length }}
        </div>
      </div>
    </div>

    <q-scroll-area class="col q-my-md">

    <q-card
      v-for="i in listItems"
      :key="i.product_code"
      v-touch-hold.mouse="() => showItemReferences = i"
      class="surface1 q-pa-md q-mb-sm row items-center text-body1"
      :class="i.qt_planned === i.qt_confirmed ? 'theme-green' : 'surface1'"
      @click.stop="() => i.status === 'planned' ? selectItem(i) : null"
    >
      <div class="col-8 column" style="min-width: 0">
        <div class="col">
          <div class="text-h4 highlight">
            {{ i.product_code }}
          </div>
          <div class="smaller ellipsis" style="line-height: 1rem; max-width: 60vw;">
            {{ i.product_description }}
          </div>
          <div
            v-if="i.references.purchase_doc"
            class="text-h6 text-low uppercase q-mt-xs">
            {{ i.references.purchase_doc }}
          </div>
        </div>
      </div>
      <q-space></q-space>

      <div class="col-auto column full-height justify-between q-col-gutter-y-sm">
        <div class="col-auto self-end row q-gutter-x-sm items-center">
          <div class="col-auto highlight">
            {{ i.qt_planned - i.qt_confirmed }} / {{ i.qt_planned }}
          </div>
        </div>
        <div class="col-auto row items-center text-low justify-end">
          <q-icon v-if="i.type === 'serial'" name="mdi-cube-scan" size="xs"/>
          <q-icon v-else name="mdi-apps" size="xs"/>
          <template v-if="i.status === 'completed'">
            <q-icon name="mdi-arrow-right-thin" />
            <div class="text-h5">{{ i.position_to }}</div>
          </template>
        </div>
      </div>
      <q-linear-progress
        class="absolute-bottom"
        :value="i.qt_confirmed / i.qt_planned"
        color="theme-blue"
        track-color="theme-grey"
        :thickness=".2"
        size="xs"
      />
    </q-card>
    </q-scroll-area>

    <div class="row q-col-gutter-x-sm">
      <div class="col-6">
        <q-btn
          color="theme-grey"
          :label="$t('back')"
          class="full-width"
          @click="$router.push({ name: 'IncomingHome'})"
        />
      </div>
      <div class="col-6">
        <q-btn
          color="theme-blue"
          :label="$t('confirm')"
          class="full-width"
          @click="closeList"
        />
      </div>
    </div>

    <SlideUpCard
      :model-value="showItemReferences !== false"
      @hide="() => showItemReferences=false"
    >
      <div class="text-h4 highlight q-mb-md">
        {{ showItemReferences.product_code }}
      </div>
      <div
        v-for="([ref, value]) in Object.entries(showItemReferences.references)"
        :key="ref"
      >
        {{ ref }}: <span class="highlight">{{ value }}</span>
      </div>
    </SlideUpCard>


    <IncomingItem v-if="lists.selectedItem !== undefined" />
  </q-page>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useListsStore } from 'stores/lists';
import { useI18n } from 'vue-i18n';
import SlideUpCard from 'app/src/components/SlideUpCard.vue';
import { Dialog } from 'quasar';
import { sendEvent } from 'app/src/composables/event';
import { useNavStore } from 'app/src/stores/navigation';
import { onBeforeRouteLeave, useRouter } from 'vue-router';
import IncomingItem from './IncomingItem.vue';

const lists = useListsStore();
const { t: $t } = useI18n();
const nav = useNavStore();
const $router = useRouter();

const props = defineProps({
  listKey: String
});

const showItemReferences = ref(false)

const list = lists.headers.find(l => l._key == props.listKey);

if (list === undefined) {
  $router.push({ name: 'IncomingHome'})
}

nav.dynamicBreadcrumb = [list?.code]
onBeforeRouteLeave(() => {
  nav.dynamicBreadcrumb = []
})

const listItems = computed(() => lists.movementsByListAndProduct[props.listKey]);

function selectItem(item) {
  lists.selectedItem = JSON.parse(JSON.stringify(item))
}


function closeList() {
  // Retrieve all movements with qt_confrimed > 0 and status planned, send as movement with
  const updatedMovements = lists?.movements?.filter(m => m.status === 'planned' && m.qt_confirmed > 0)

  // Ask to keep open or not if qt_confirmed < qt_planned
  Dialog.create({
    message: "Confermi di voler registrare i ricevimenti indicati?",
    cancel: { label: $t('cancel'), color: 'theme-grey'},
    ok: { label: $t('confirm'), color: 'theme-blue'}
  }).onOk(() => {
    // let keepOpen = false;
    Dialog.create({
      message: "Vuoi mantenere aperti i movimenti pianificati rimanenti?",
      cancel: { label: $t('no'), color: 'theme-orange'},
      ok: { label: $t('yes'), color: 'theme-blue'}
    }).onOk(() => {
      console.log('saving')
      for (const update of updatedMovements) {
        sendEvent({
          event_type: 'MOVEMENT_CONFIRMED',
          event_data: {
            movement_update: update
          },
        })
      }})
      .onCancel(() => console.log('Close partial movements'))
    })
    .onCancel(() => {
      console.log('canceled')
    })
  }
</script>
