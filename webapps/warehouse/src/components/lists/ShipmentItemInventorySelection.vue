<template>
  <div class="column col q-gutter-y-md full-width">

    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto row">
      <div class="col">
        <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
        <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
          {{ lists.selectedItem?.product_code }}
        </div>
        <div class="text-body2 smaller q-mt-xs">
          {{ lists.selectedItem?.product_description }}
        </div>
      </div>
      <div class="col-auto text-right">
        <div class="text-h6 q-mb-sm">
          Quantità
        </div>
        <div class="text-h3">
          {{ shipment.shipmentQuantity }} / {{ lists.selectedItem?.qt_planned - lists.selectedItem?.qt_confirmed }}
        </div>
      </div>
    </div>

    <!-- ITEMS WITH TRACEABILITY AND SERIALS SPECIFIED -->
    <div class="col column" v-if="requestedSerials.length > 0">
      <div class="row items-center q-gutter-x-xs">
        <div class="text-h2 col-auto">
          Seriali richiesti
        </div>
        <q-space></q-space>
        <q-btn color="theme-grey" size="xs" padding="xs md" icon="mdi-checkbox-multiple-blank-outline" @click="() => toggleAll(false)" />
        <q-btn color="theme-blue" size="xs" padding="xs md" icon="mdi-checkbox-multiple-marked" @click="() => toggleAll(true)" />
      </div>

      <SearchOrScan
        v-model="serialFilter"
        class="q-my-md"
        label="Scansiona o ricerca posizione"
        @update:model-value="filterSerials"
      />

      <q-scroll-area class="col scroll">
        <q-list>
          <q-item
            v-for="item in shownSerials"
            :key="item.serial_key"
            :clickable="item.available"
            :disabled="!item.available"
            class="content-card q-my-sm q-pa-md text-body1"
            :class="backgroundClass(item)"
            @click="onItemClick(item)"
          >
            <q-item-section side>
              <q-icon name="mdi-cube-scan" :color="item.available ? 'high' : 'low'" />
            </q-item-section>
            <q-item-section>
              <q-item-label>
                {{  item.serial_code }}
              </q-item-label>
              <q-item-label caption>
                {{ item.path.map(p => p.position_code).join(' → ') || 'Non disponibile' }}
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-icon :name="item.icon.name" :color="item.icon.color"/>
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </div>

    <!-- OTHER ITEMS -->
    <div class="col column" v-else>
      <div class="text-h2 col-auto">
        Materiale disponibile
      </div>

      <SearchOrScan
        v-model="inventoryFilter"
        class="q-my-md"
        label="Filtra per seriale o posizione"
        @update:model-value="filterInventory"
      />

      <q-scroll-area class="col scroll">
        <q-list>
          <q-item
            v-for="item in shownInventory"
            :key="item._key"
            clickable
            :disabled="isDisabled(item)"
            class="content-card q-my-sm q-pa-md text-body1"
            :class="backgroundClass(item)"
            @click="onItemClick(item)"
          >
            <q-item-section side>
              <q-icon :name="lists.selectedItem.type === 'serial' ? 'mdi-cube-scan' : 'mdi-apps'" />
            </q-item-section>
            <q-item-section>
              <q-item-label>
                {{  item.serial_code ? item.serial_code : item.product_code }}
              </q-item-label>
              <q-item-label caption>
                {{ item.path.map(p => p.position_code).join(' → ') || 'IN' }}
              </q-item-label>
            </q-item-section>
            <q-item-section side v-if="item.serial_code">
              <q-icon
                v-if="!isDisabled(item)"
                :name="selectedSerials.includes(item.serial_code) ? 'mdi-check-circle' : 'mdi-circle-outline'"
                :color="selectedSerials.includes(item.serial_code) ? 'white' : 'low'"
              />
            </q-item-section>
            <q-item-section side v-else class="highlight">
              {{ shipment.inventorySelectedQt(item._key) }} / {{ item.quantity }}
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>
    </div>

    <q-space></q-space>

    <SlideUpCard
      :model-value="cardItem !== null"
      @hide="onCardHide"
      height="400px"
    >
        <!-- QUANTITY -->
      <QuantitySelector
        v-model="inventoryItemTempQuantity"
        heading="Quantità da confermare"
        :max="maxSelectableQuantity"
        show-buttons
        class="col"
      />
      <q-btn color="theme-blue" class="q-mt-md" label="seleziona" @click="selectItemQuantity" />

    </SlideUpCard>

  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useShipmentStore } from '@/stores/shipment';
import { useListsStore } from 'stores/lists';
import QuantitySelector from '@/components/QuantitySelector.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';
import SearchOrScan from '@/components/SearchOrScan.vue';
import { Notify } from 'quasar';
// import { useRouter } from 'vue-router';

// const router = useRouter();

const shipment = useShipmentStore();
const lists = useListsStore();

shipment.product = { _key: lists.selectedItem.product_key };
shipment.loadInventory();

const inventoryFilter = ref('');
const serialFilter = ref('');


const itemMovements = computed(() => lists.selectedItem.movements);

const requestedSerials = computed(() => {
  return itemMovements.value.filter(m => m.status === 'planned' && m.serial_code).map(m => {
    const serialInventory = shipment.inventory?.find(i => i.serial_code === m.serial_code);
    let icon
    if (serialInventory) {
      const isSelected = selectedSerials.value.includes(m.serial_code);
      icon = isSelected ? {
        name: 'mdi-check-circle',
        color: 'white'
      } : {
        name: 'mdi-circle-outline',
        color: 'theme-grey'
      };
    } else {
      icon = {
        name: 'mdi-alert-outline',
        color: 'theme-orange'
      };
    }
    return {
      ...m,
      available: serialInventory ? true : false,
      path: serialInventory ? serialInventory.path : [],
      icon
    };
  });
});

function isDisabled(item) {
  return shipment.shipmentQuantity >= lists.selectedItem.qt_planned - lists.selectedItem.qt_confirmed
  && !shipment.selectedInventory.map(i => i._key).includes(item._key)
}

const shownSerials = computed(() => {
  return requestedSerials.value.filter(s => s.serial_code.toLowerCase().includes(serialFilter.value.toLowerCase()));
});

const selectedSerials = computed(() => {
  return shipment.selectedInventory.map(i => i.serial_code);
});


function getInventoryFilterContext(item) {
  const positions = item.path.map(p => p.position_code).join(' ') || 'IN'
  const serial = item.serial_code
  return `${serial} ${positions}`
}

const shownInventory = computed(() => {
  if (inventoryFilter.value) {
    return shipment.inventory.filter(i => getInventoryFilterContext(i).toLowerCase().includes(inventoryFilter.value.toLowerCase()));
  }
  return shipment.inventory;
});

const cardItem = ref(null);
const inventoryItemTempQuantity = ref(0);

const maxSelectableQuantity = computed(() => {
  const inventoryMax = shipment.inventory.find(i => i._key === cardItem.value).quantity;
  const inventorySelected = shipment.selectedInventory.find(i => i._key === cardItem.value)?.selected || 0;
  return Math.min(lists.selectedItem.qt_planned - lists.selectedItem.qt_confirmed - shipment.shipmentQuantity + inventorySelected, inventoryMax);
});

function filterSerials(value) {
  if (shownSerials.value.length === 1 && shownSerials.value[0].serial_code === value) {
    toggleSerial(value);
    resetInput();
  }
}

function filterInventory(value) {
  if (shownInventory.value.length === 1 && shownInventory.value[0].path.map(p => p.position_code).some(p => p === value)) {
    onItemClick(shownInventory.value[0]);
    resetInput();
  }
}

function resetInput() {
  serialFilter.value = ''
  document.getElementById('search-input').focus()
}

function backgroundClass(item) {
  if (item.available === false) {
    return 'content-card-unavailable'
  }
  const color = item.serial_code ? 'green' : 'blue'
  const isSelected = shipment.selectedInventory.find(i => i._key === item._key)
  return isSelected ? `bg-theme-${color}` : `bg-${color}-backdrop`
}

function onItemClick(item) {
  if (isDisabled(item)) {
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: `Quantità massima raggiunta`,
      timeout: 2000
    })
    return
  }
  if (item.serial_key) {
    // Select or unselect serial
    toggleSerial(item);
  }
  else {
    // Set inventory among selected if necessary and pass inventory key to quantity selector
    cardItem.value = item._key;
    const match = shipment.selectedInventory.find(i => i._key === item._key);
    inventoryItemTempQuantity.value = match ? match.selected : 0;
  }
}

function selectSerial(inventoryItem) {
  shipment.selectedInventory.push({
    ...inventoryItem,
    selected: 1
  });
  lists.tempQuantity += 1;
  resetInput()
}

function toggleSerial(inventoryItem) {
  const inventoryMatch = shipment.selectedInventory.findIndex(i => i._key === inventoryItem._key);

  if (inventoryMatch !== -1) {
    shipment.selectedInventory.splice(inventoryMatch, 1);
    resetInput()
  }
  else {
    if (requestedSerials.value.length === 0) {
      selectSerial(inventoryItem)
    }
    else { // Check whether serial is among requested serials

      const movementMatch = itemMovements.value.findIndex(m => m.serial_code === inventoryItem.serial_code);
      if (movementMatch === -1) { // Serial not found among requested serials
        Notify.create({
          position: 'top',
          color: 'theme-orange',
          message: `Seriale ${inventoryItem.serial_code} non presente fra quelli previsti`,
          timeout: 2000
        })
      }
      else {
        selectSerial(inventoryItem)
      }
    }
  }
}


function toggleAll(select = true) {
  if (select) {
    // Add all available items that aren't already selected
    shownSerials.value.forEach(item => {
      if (item.available && !selectedSerials.value.includes(item.serial_code)) {
        if (requestedSerials.value.length === 0) {
          selectSerial(item);
        } else {
          // Only select if serial is among requested serials
          const movementMatch = itemMovements.value.find(m => m.serial_code === item.serial_code);
          if (movementMatch) {
            selectSerial(item);
          }
        }
      }
    });
  } else {
    // Remove all shown items from selection
    const shownSerialCodes = shownSerials.value.map(s => s.serial_code);
    shipment.selectedInventory = shipment.selectedInventory.filter(
      item => !item.serial_code || !shownSerialCodes.includes(item.serial_code)
    );
    resetInput();
  }
}



function selectItemQuantity() {
  const match = shipment.selectedInventory.findIndex(i => i._key === cardItem.value);
  if (match === -1) {
    shipment.selectedInventory.push({
      ...shipment.inventory.find(i => i._key === cardItem.value),
      selected: inventoryItemTempQuantity.value
    });
  }
  else {
    if (inventoryItemTempQuantity.value === 0) {
      shipment.selectedInventory.splice(match, 1);
    }
    else {
      shipment.selectedInventory[match].selected = inventoryItemTempQuantity.value;
    }
  }
  cardItem.value = null;
}


function onCardHide() {
  cardItem.value = null;
  inventoryItemTempQuantity.value = 0;
}

</script>

<style scoped lang="sass">
.content-card
  border-radius: 5px

.content-card-unavailable
  border: 1px solid var(--box-border)
</style>
