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
          {{ list?.type === 'receipt' ? 'Verificati' : 'Completati' }}
        </div>
        <div class="text-right text-body1">
          {{ listItems?.filter(i => i.qt_confirmed >= i.qt_planned).length }} / {{  listItems?.length }}
        </div>
      </div>
    </div>

    <SearchOrScan v-model="productSearch" label="Filtra prodotti" class="q-mt-md" />

    <q-scroll-area class="col q-my-md">

    <q-card
      v-for="i in listItems"
      :key="i.item"
      v-touch-hold.mouse="() => showItemReferences = i"
      class="surface1 q-pa-md q-mb-sm row items-start text-body1 col-auto"
      :style="i.qt_planned <= i.qt_confirmed ? 'opacity: 0.5' : ''"
      @click.stop="() => i.qt_planned > i.qt_confirmed ? selectItem(i) : null"
    >
      <div class="col column" style="min-width: 0">
        <!-- PRODUCT DATA -->
        <div class="col row items-center">
          <q-icon v-if="i.qt_confirmed >= i.qt_planned" name="mdi-check-circle" color="theme-green" size="xs"/>
          <q-icon v-else-if="i.type === 'serial'" name="mdi-cube-scan" size="xs"/>
          <q-icon v-else name="mdi-apps" size="xs"/>
          <div class="text-h4 highlight q-ml-sm">
            {{ i.product_code }}
          </div>
        </div>
        <div class="smaller ellipsis q-mt-xs" style="line-height: 1rem; max-width: 60vw;">
          {{ i.product_description }}
        </div>
        <div
          v-if="i.reference"
          class="text-h6 text-low uppercase q-mt-xs">
          {{ i.reference }}
        </div>

        <!-- COMPLETED MOVEMENTS -->
        <div v-if="i.movements.some(m => m.status === 'completed')" class="q-mt-sm">
          <div
            v-for="(group, index) in getCompletedMovementsSummary(i.movements)"
            :key="index"
            class="row items-center full-height text-caption text-low q-gutter-x-sm"
            :class="{ 'reverse justify-end': list.type === 'shipment' }"
          >
            <div class="col-auto">
              {{ group.date }}
            </div>
            <div class="col-auto">
              {{ group.qt_confirmed }}x
            </div>
            <q-icon name="mdi-arrow-right-thin" size="xs"/>
            <div class="col-auto">
              {{ group.position_code }}
            </div>
          </div>
        </div>
      </div>
      <q-space></q-space>

      <!-- QUANTITY CONFIRMED/PLANNED -->
      <div class="col-auto row items-center highlight">
        {{ i.qt_confirmed }} / {{ i.qt_planned }}
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
          @click="$router.push({ name: list.type === 'receipt' ? 'IncomingHome' : 'ShipmentHome'})"
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

    <template v-if="lists.selectedItem !== undefined">
      <IncomingItem v-if="list.type === 'receipt'" />
      <ShipmentItem v-else />
    </template>
  </q-page>
</template>

<script setup>
import { Dialog, Notify } from 'quasar';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router';
import SearchOrScan from 'app/src/components/SearchOrScan.vue';
import { sendEvent } from 'app/src/composables/event';
import { useNavStore } from 'app/src/stores/navigation';
import IncomingItem from 'app/src/views/incoming/IncomingItem.vue';
import ShipmentItem from 'app/src/views/shipment/ShipmentItem.vue';
import { useListsStore } from 'stores/lists';
const lists = useListsStore();
const { t: $t } = useI18n();
const nav = useNavStore();
const $router = useRouter();
const $route = useRoute();

const props = defineProps({
  listKey: {
    type: String,
    required: true
  }
});

const showItemReferences = ref(false)

const list = lists.headers.find(l => l._key == props.listKey);

if (list === undefined) {
  $router.push({ name: $route.matched.some(m => m.name === 'ShipmentRoot') ? 'ShipmentHome' : 'IncomingHome'})
}

const productSearch = ref('');

nav.dynamicBreadcrumb = [list?.code]
onBeforeRouteLeave(() => {
  nav.dynamicBreadcrumb = []
})

const listItems = computed(() => {
  // Sort items placing completed ones at the end
  const items = lists.movementsByListAndItem[props.listKey] ?? [];
  const openItems = items.filter(i => i.qt_planned > i.qt_confirmed);
  const closedItems = items.filter(i => i.qt_planned <= i.qt_confirmed);
  return [...openItems, ...closedItems]
    .filter(i => productSearch.value ? i.product_code.toLowerCase().includes(productSearch.value.toLowerCase()) : true)
});

function selectItem(item) {
  lists.selectedItem = JSON.parse(JSON.stringify(item))
}

function getCompletedMovementsSummary(movements) {
  const groups = Object.groupBy(
    movements.filter(m => m.status === 'completed'),
    (m) => {
      const date = new Date(m.end).toLocaleDateString()
      const position_code = list.type === 'receipt' ? m.position_to_code : m.position_from_code
      return `${date}-${position_code}`
    }
  )
  return Object.entries(groups).map(([key, value]) => {
    return {
      date: key.split('-')[0],
      position_code: key.split('-')[1],
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
      lists.loadLists(list.type)
      $router.push({ name: list.type === 'shipment' ? 'ShipmentHome' : 'IncomingHome'})
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
