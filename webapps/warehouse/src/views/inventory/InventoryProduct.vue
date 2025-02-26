<template>
  <div class="col column full-width q-col-gutter-y-sm">
    <ProductSearch v-if="selectedProduct === null" @select="selectProduct" />

    <!-- Product inventory -->
    <template v-else>
      <div class="text-h2 col-auto">
        {{ selectedProduct.code }}
      </div>
      <div class="text-body2 col-auto">
        {{ selectedProduct.description }}
      </div>

      <div class="row col-auto q-col-gutter-x-sm">
        <q-input
          v-model="positionFilter"
          class="q-my-sm col"
          filled
          dense
          :debounce="300"
          label="Filtra per posizione"
          @update:model-value="loadInventory"
        />
        <q-input
          v-if="selectedProduct.traceability_level"
          v-model="serialFilter"
          class="q-my-sm col"
          filled
          dense
          label="Filtra per seriale"
          :debounce="300"
          @update:model-value="loadInventory"
        />
      </div>

      <div class="text-h6 col-auto q-mt-sm">
        {{ inventory.contents.length ? 'Materiale disponibile' : 'Nessun materiale disponibile' }}
      </div>

      <q-scroll-area v-if="inventory.contents.length > 0" class="col q-mt-md">
        <q-list>
          <q-item
            v-for="item in inventory.contents"
            :key="item._key"
            :clickable="item.serial_key === null"
            class="content-card q-my-sm q-pa-md text-body1"
            :class="backgroundClass(item)"
            @click="onItemClick(item)"
          >
            <q-item-section side>
              <q-icon :name="item.serial_key ? 'mdi-cube-scan' : 'mdi-apps'" />
            </q-item-section>
            <q-item-section>
              <q-item-label class="highlight">
                {{  item.serial_code ? item.serial_code : item.product_code }}
              </q-item-label>
              <q-item-label caption>
                {{ item.path.map(p => p.position_code).join(' → ') || 'IN' }}
              </q-item-label>
            </q-item-section>
            <q-item-section v-if="item.serial_key === null" side>
              <div class="text-body2">
                {{ item.quantity }}
              </div>
            </q-item-section>
          </q-item>
        </q-list>
      </q-scroll-area>

      <q-space></q-space>
      <q-btn color="theme-blue" class="q-mt-md" :label="$t('back')" @click="selectedProduct = null" />


      <SlideUpCard
        :model-value="cardItem !== null"
        @hide="resetSelection"
        height="450px"
      >
          <!-- QUANTITY -->
        <QuantitySelector
          v-model="inventoryItemTempQuantity"
          heading="Quantità da confermare"
          show-buttons
          class="col"
        >
          <template #heading>
            <div class="col">
              <div class="text-h3">Modifica quantità</div>
              <div class="text-h3">{{ cardItem.code }}</div>
            </div>
            <div class="col-auto highlight">
              <q-chip
                size="md"
                :color="adjustmentQuantity === 0 ? 'theme-grey' : (adjustmentQuantity > 0 ? 'theme-green' : 'theme-orange')"
                :label="(adjustmentQuantity > 0 ? '+' : '') + adjustmentQuantity"
                class="full-width"
              />
            </div>
          </template>
        </QuantitySelector>
        <q-btn color="theme-blue" outline class="q-mt-md" label="Reimposta" @click="inventoryItemTempQuantity = cardItem.quantity" />
        <q-btn color="theme-blue" class="q-mt-md" label="Aggiorna quantità" @click="confirmQuantity" />

      </SlideUpCard>
    </template>

  </div>
</template>

<script setup>
import SlideUpCard from '@/components/SlideUpCard.vue';
import QuantitySelector from '@/components/QuantitySelector.vue';
import ProductSearch from '@/components/ProductSearch.vue';
import { Notify } from 'quasar'
import { timestamp } from '@/lib/TimeHandling';
import { sendEvent } from '@/composables/event';
// import { useI18n } from 'vue-i18n';
import { ref, computed } from 'vue';
import { useInventoryStore } from '@/stores/inventory';

const inventory = useInventoryStore();

// const { t } = useI18n();

const cardItem = ref(null);
const inventoryItemTempQuantity = ref(1);
const positionFilter = ref(null);
const serialFilter = ref(null);
const selectedProduct = ref(null);



function selectProduct(product) {
  selectedProduct.value = product;
  inventoryItemTempQuantity.value = 0;
  inventory.loadInventory({ product_key: product._key });
}

function loadInventory() {
  inventory.loadInventory({
    product_key: selectedProduct.value._key,
    position_search: positionFilter.value,
    serial_search: serialFilter.value
  });
}

const adjustmentQuantity = computed(() => inventoryItemTempQuantity.value - cardItem.value.quantity);

function backgroundClass(item) {
  const color = item.serial_code ? 'green' : 'blue'
  return `bg-${color}-backdrop`
}

function onItemClick(item) {
  // Set inventory among selected if necessary and pass inventory key to quantity selector
  cardItem.value = item;
  inventoryItemTempQuantity.value = item.quantity;
}

function resetSelection() {
  cardItem.value = null;
  inventoryItemTempQuantity.value = 0;
}

function confirmQuantity() {
  const now = timestamp();
  sendEvent({
    event_type: 'MOVEMENT_COMPLETED',
    event_data: {
      position_from: cardItem.value.path.slice(-1)[0].position_key,
      position_to: cardItem.value.path.slice(-1)[0].position_key,
      product_key: cardItem.value.product_key,
      qt_planned: adjustmentQuantity.value,
      qt_confirmed: adjustmentQuantity.value,
      status: 'completed',
      movement_type: 'adjustment',
      start: now,
      end: now,
    }
  })
  .then(() => {
    inventory.loadInventory({ product_key: selectedProduct.value._key });
    resetSelection();
    Notify.create({
      message: 'Quantità aggiornata',
      color: 'theme-green',
      position: 'top',
    });
  })
}
</script>

<style lang="scss" scoped>

</style>
