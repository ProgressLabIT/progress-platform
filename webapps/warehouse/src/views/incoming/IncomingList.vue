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
          Verificati
        </div>
        <div class="text-right text-body1">
          {{ listItems?.filter(i => i.qt_confirmed >= i.qt_planned).length }} / {{  listItems?.length }}
        </div>
      </div>
    </div>

    <q-scroll-area class="col q-my-md">

    <q-card
      v-for="i in listItems"
      :key="i.product_code"
      v-touch-hold.mouse="() => showItemReferences = i"
      class="surface1 q-pa-md q-mb-sm row items-center text-body1 col-auto"
      :class="i.qt_planned <= i.qt_confirmed ? 'theme-green' : 'surface1'"
      :style="i.qt_planned <= i.qt_confirmed ? 'opacity: 0.5' : ''"
      @click.stop="() => i.qt_planned > i.qt_confirmed ? selectItem(i) : null"
    >
      <div class="col-8 column" style="min-width: 0">
        <!-- PRODUCT DATA -->
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

        <!-- COMPLETED MOVEMENTS -->
        <div v-if="i.movements.some(m => m.status === 'completed')" class="q-mt-sm">
          <div
            v-for="(group, index) in getCompletedMovementsSummary(i.movements)"
            :key="index"
            class="row items-center full-height text-caption text-low q-gutter-x-sm"
          >
            <div class="col-auto">
              {{ group.date }}
            </div>
            <div class="col-auto">
              {{ group.qt_confirmed }}x
            </div>
            <q-icon name="mdi-arrow-right-thin" size="xs"/>
            <div class="col-auto">
              {{ group.position_to_code }}
            </div>
          </div>
        </div>
      </div>
      <q-space></q-space>

      <!-- QUANTITY CONFIRMED/PLANNED -->
      <div class="absolute-top-right q-mt-md q-mr-md highlight">
        {{ i.qt_confirmed }} / {{ i.qt_planned }}
      </div>
      <div class="absolute-bottom-right q-mb-md q-mr-md">
        <q-icon v-if="i.qt_confirmed >= i.qt_planned" name="mdi-check-circle" color="theme-green" size="xs"/>
        <q-icon v-else-if="i.type === 'serial'" name="mdi-cube-scan" size="xs"/>
        <q-icon v-else name="mdi-apps" size="xs"/>
      </div>

      <q-linear-progress
        class="absolute-bottom"
        :value="i.qt_confirmed / i.qt_planned"
        color="theme-blue"
        track-color="theme-grey"
        :thickness=".5"
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
          :label="$t('close')"
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
import { Dialog, Notify } from 'quasar';
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

const listItems = computed(() => lists.movementsByListAndItem[props.listKey]);

function selectItem(item) {
  lists.selectedItem = JSON.parse(JSON.stringify(item))
}

function getCompletedMovementsSummary(movements) {
  const groups = Object.groupBy(
    movements.filter(m => m.status === 'completed'),
    (m) => `${new Date(m.end).toLocaleDateString()}-${m.position_to_code}`
  )
  return Object.entries(groups).map(([key, value]) => {
    return {
      date: key.split('-')[0],
      position_to_code: key.split('-')[1],
      qt_confirmed: value.reduce((acc, m) => acc + m.qt_confirmed, 0),
    }
  })
}


function closeList() {
  // Ask to keep open or not if qt_confirmed < qt_planned
  Dialog.create({
    message: "Confermi di voler chiudere la lista nello stato attuale?",
    cancel: { label: $t('cancel'), color: 'theme-grey'},
    ok: { label: $t('confirm'), color: 'theme-blue'}
  }).onOk(() => {
    sendEvent({
      event_type: 'WAREHOUSE_LIST_CLOSED',
      event_data: {
        movement_list_key: props.listKey
      },
    }).then(() => {
      lists.loadLists()
      $router.push({ name: 'IncomingHome'})
    }).catch((error) => {
      Notify.create({
        position: 'top',
        color: 'theme-orange',
        message: "Si è verificato un errore: " + error.message,
        timeout: 0,
        actions: [{
          label: $t('close'),
          color: 'white',
          handler: () => undefined
        }]
      })
    })
  })
  .onCancel(() => {
    console.log('canceled')
  })
  }
</script>
