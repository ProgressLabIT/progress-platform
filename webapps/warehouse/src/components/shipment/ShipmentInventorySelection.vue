<template>
  <div class="column col q-gutter-y-md full-width">

    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto">
      <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
      <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
        {{ shipment.product?.code }}
      </div>
      <div class="text-body2 smaller q-mt-xs">
        {{ shipment.product?.description }}
      </div>
    </div>

    <!-- Contents search / selection -->
    <div class="text-h2">{{ $t('transfer_contents_select')}}</div>
    <div class="row q-col-gutter-sm">
      <q-input
        v-model="positionFilter"
        filled
        dense
        label="Filtro posizione"
        class="col"
        :debounce="300"
        @update:model-value="filterResults"
      />
      <q-input
        v-if="shipment.product?.type === 'serial'"
        v-model="serialFilter"
        filled
        dense
        label="Filtro seriale"
        class="col-6"
        :debounce="300"
        @update:model-value="filterResults"
      />
    </div>

    <template v-if="shipment.inventory.length === 0">
      <div class="text-body2">{{ $t('no_results')}}</div>
    </template>

    <q-scroll-area v-else class="col scroll q-mt-md">
      <q-card
        v-for="item in shipment.inventory"
        :key="item._key"
        clickable
        class="content-card q-my-xs q-pa-md text-body1"
        :class="getColor(item)"
        @click="onItemClick(item)"
      >
        <div class="row items-center q-col-gutter-md">
          <!-- ITEM TYPE -->
          <div class="col-auto">
            <q-icon v-if="item.selected === item.quantity" name="mdi-check-circle" size="xs"/>
            <q-icon v-else-if="item.serial_key" name="mdi-cube-scan" size="xs"/>
            <q-icon v-else name="mdi-apps" size="xs"/>
          </div>

        <!-- WAREHOUSE PATH -->
        <div class="col column">
          <div v-if="item.serial_key" class="col-auto highlight text-right">
            {{ item.serial_code }}
          </div>
          <div v-else class="col-auto highlight text-right">
            {{ shipment.inventorySelectedQt(item._key) }} / {{ item.quantity }}
            </div>
          </div>
          <div class="row items-center full-height q-gutter-x-sm" style="min-width: 0">
            <template
              v-for="(position, index) in item.path"
              :key="index"
            >
            <div class="col-auto">
              {{ position.position_code }}
            </div>
            <q-icon
              v-if="index < item.path.length - 1"
              name="mdi-arrow-right-thin"
              size="xs"
              class="col-auto"
            />
            </template>
          </div>
        </div>
      </q-card>
    </q-scroll-area>


    <q-space></q-space>

    <q-btn :disable="shipment.selectedInventory.length === 0" color="theme-blue" :label="$t('next')" @click="next" />
    <q-btn color="theme-grey" :label="$t('cancel')" @click="cancel" />

    <SlideUpCard
      :model-value="cardItem !== null"
      @hide="onCardHide"
    >
      <!-- Select product quantity -->
      <QuantitySelector
        v-model="tempQuantity"
        show-buttons
        selector-style="min-height: 100px;"
        :min="0"
        :max="getCurrentItem?.quantity || 0"
      />
      <q-btn color="theme-blue" class="q-mt-md" label="seleziona" @click="selectItemQuantity" />
    </SlideUpCard>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useShipmentStore } from '@/stores/shipment';
import QuantitySelector from '@/components/QuantitySelector.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const shipment = useShipmentStore();

const positionFilter = ref('');
const serialFilter = ref('');
const cardItem = ref(null);
const tempQuantity = ref(0);

const getCurrentItem = computed(() => {
  if (!cardItem.value) {
    return null;
  }
  return shipment.inventory.find(i => i._key === cardItem.value);
});

function getColor(item) {
  const color = item.serial_key ? 'green' : 'blue'
  return shipment.inventorySelectedQt(item._key) > 0 ? `bg-theme-${color}` : `bg-${color}-backdrop`
}

async function filterResults() {
  shipment.loadInventory(positionFilter.value, serialFilter.value);
}


function onItemClick(item) {
  if (item.serial_key) {
    // Select or unselect serial
    toggleSerial(item);
  }
  else {
    // Set inventory among selected if necessary and pass inventory key to quantity selector
    const match = shipment.selectedInventory.findIndex(i => i._key === item._key);
    if (match === -1) {
      shipment.selectedInventory.push({
        _key: item._key,
        selected: 0
      });
      cardItem.value = item._key;
      tempQuantity.value = 0;
    }
    else {
      cardItem.value = item._key;
      tempQuantity.value = shipment.selectedInventory[match].selected;
    }
  }
}

function toggleSerial(item) {
  const match = shipment.selectedInventory.findIndex(i => i._key === item._key);
  if (match === -1) {
    shipment.selectedInventory.push({
      _key: item._key,
      selected: 1
    });
  } else {
    shipment.selectedInventory.splice(match, 1);
  }
}

function selectItemQuantity() {
  const match = shipment.selectedInventory.findIndex(i => i._key === cardItem.value);
  if (tempQuantity.value > 0) {
    shipment.selectedInventory[match].selected = tempQuantity.value;
  }
  else {
    // Remove item from selected inventory if quantity is 0
    shipment.selectedInventory.splice(match, 1);
  }
  cardItem.value = null;
}

function next() {
  shipment.stage = 'confirm';
}

function cancel() {
  shipment.$reset()
  router.push({ name: 'ShipmentRoot'})
}

function onCardHide() {
  cardItem.value = null;
  tempQuantity.value = 0;
}

</script>

<style scoped lang="sass">
.content-card
  border-radius: 5px
</style>
