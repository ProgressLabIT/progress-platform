<template>
  <div class="col column q-pb-sm">
    <div class="text-h2 col-auto">
      {{ transfer.product.code }}
    </div>
    <div class="text-h6 col-auto q-mt-sm">
      {{ shownInventory.length ? 'Materiale disponibile' : 'Nessun materiale disponibile' }}
    </div>

    <SearchOrScan
      v-model="inventoryFilter"
      v-if="inventory.length > 0"
      class="q-my-md"
      label="Filtra per seriale o posizione"
    />

    <q-scroll-area class="col scroll">
      <q-list>
        <q-item
          v-for="item in shownInventory"
          :key="item._key"
          clickable
          class="content-card q-my-sm q-pa-md text-body1"
          :class="backgroundClass(item)"
          @click="onItemClick(item)"
        >
          <q-item-section side>
            <q-icon :name="item.type === 'serial' ? 'mdi-cube-scan' : 'mdi-apps'" />
          </q-item-section>
          <q-item-section>
            <q-item-label class="highlight">
              {{  item.serial_code ? item.serial_code : item.product_code }}
            </q-item-label>
            <q-item-label caption>
              {{ item.path.map(p => p.position_code).join(' → ') || 'IN' }}
            </q-item-label>
          </q-item-section>
          <q-item-section side v-if="item.serial_code">
            <q-icon
              :name="transfer.contents.some(i => i._key === item._key) ? 'mdi-check-circle' : 'mdi-circle-outline'"
              :color="transfer.contents.some(i => i._key === item._key) ? 'white' : 'low'"
            />
          </q-item-section>
          <q-item-section v-if="item.type === 'product'" side>
            <div class="text-body2">
              <span class="highlight">
                {{ getItemSelectedQty(item) }}
              </span> / {{ item.quantity }}
            </div>
          </q-item-section>
        </q-item>
      </q-list>
    </q-scroll-area>

    <q-space />

    <div class="row q-gutter-x-sm">
      <q-btn color="theme-grey" class="col" :label="t('back')" @click="back" />
      <q-btn color="theme-blue" class="col" :label="t('next')" @click="next" />
    </div>

    <SlideUpCard
      :model-value="cardItem !== null"
      @hide="onCardHide"
      height="400px"
    >
        <!-- QUANTITY -->
      <QuantitySelector
        v-model="inventoryItemTempQuantity"
        heading="Quantità da confermare"
        :max="cardItem.quantity"
        show-buttons
        class="col"
      />
      <q-btn color="theme-blue" class="q-mt-md" label="seleziona" @click="selectItemQuantity" />

    </SlideUpCard>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import QuantitySelector from '@/components/QuantitySelector.vue';
import SearchOrScan from '@/components/SearchOrScan.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';
import { useTransferStore } from '@/stores/transfer';
import { api } from 'app/src/boot/axios';
import { useI18n } from 'vue-i18n';

const transfer = useTransferStore();

const { t } = useI18n();

const inventoryFilter = ref('');

const inventory = ref([]);

const shownInventory = computed(() => {
  return inventory.value.filter(item => {
    const searchContext = item.product_code + ' ' + item.serial_code + ' ' + item.path.map(p => p.position_code).join(' ');
    return searchContext.toLowerCase().includes(inventoryFilter.value.toLowerCase());
  });
});

const cardItem = ref(null);

const inventoryItemTempQuantity = ref(1);

function loadInventory() {
  api.get(`/inventory`, {
    params: {
      product_key: transfer.product._key,
    },
  }).then(response => {
    inventory.value = response.data.map(item => ({
      ...item,
      type: item.serial_key ? 'serial' : 'product' // no position option is available when selecting specific product
    }));
  });
}

loadInventory();


function backgroundClass(item) {
  if (item.available === false) {
    return 'content-card-unavailable'
  }
  const color = item.serial_code ? 'green' : 'blue'
  const isSelected = transfer.contents.find(i => i._key === item._key)
  return isSelected ? `bg-theme-${color}` : `bg-${color}-backdrop`
}

function onItemClick(item) {
  if (item.serial_key) {
    // Select or unselect serial
    toggleSerial(item);
  }
  else {
    // Set inventory among selected if necessary and pass inventory key to quantity selector
    cardItem.value = item;
    const match = transfer.contents.find(i => i._key === item._key);
    inventoryItemTempQuantity.value = match ? match.selected : 0;
  }
}

function selectSerial(inventoryItem) {
  transfer.contents.push({
    ...inventoryItem,
    type: 'serial',
    code: inventoryItem.serial_code,
    selected: 1
  });
}


function selectItemQuantity() {
  transfer.contents.push({
    ...cardItem.value,
    type: 'product',
    code: cardItem.value.product_code,
    quantity: inventoryItemTempQuantity.value,
  });
  cardItem.value = null;
  inventoryItemTempQuantity.value = 1;
}


function getItemSelectedQty(item) {
  return transfer.contents.find(c => c._key === item._key)?.quantity || 0;
}

function onCardHide() {
  cardItem.value = null;
  inventoryItemTempQuantity.value = 0;
}


function toggleSerial(inventoryItem) {
  const inventoryMatch = transfer.contents.findIndex(i => i._key === inventoryItem._key);

  if (inventoryMatch !== -1) {
    transfer.contents.splice(inventoryMatch, 1);
  }
  else {
    selectSerial(inventoryItem)
  }
}

function next() {
  transfer.stage = 'destination';
}

function back() {
  transfer.product = undefined;
  transfer.contents = [];
  transfer.stage = 'start';
}

</script>

<style lang="scss" scoped>

</style>
