<template>
  <div class="col column full-width">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="row col-auto full-width">
      <div class="col">
        <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
        <div class="text-h3 q-pr-xl" style="word-wrap: break-word">
          {{ shipment.product?.code }}
        </div>
      </div>
      <div class="col-auto">
        <div class="text-h6 text-right q-mb-sm">{{ $t('total') }}</div>
        <div class="text-h3 text-right">
          {{ totalQuantity }}
        </div>
      </div>
    </div>

    <!-- Source positions and quantities/serials -->
    <div class="row items-center justify-between q-mt-lg q-mb-md">
      <div class="text-h6">
        Origine
      </div>
      <div class="text-h6">
        {{ shipment.product.traceability_level ? 'Seriale' : $t('quantity') }}
      </div>
    </div>

    <!-- Serial items -->
    <q-scroll-area class="col full-width">
      <template v-if="shipment.product.traceability_level">
        <template v-for="item in serialItems" :key="item._key">
          <div class="row items-center q-col-gutter-x-sm q-mt-sm">
            <div class="col text-h4">
              {{ getPositionPath(item) }}
            </div>
            <div class="col-auto">
              <q-card
                flat
                class="bg-theme-green q-pa-sm highlight"
              >
                {{ item.serial_code }}
              </q-card>
            </div>
          </div>
        </template>
      </template>

      <!-- Non-serial items -->
      <template v-else>
        <template v-for="item in nonSerialItems" :key="item._key">
          <div class="row items-center q-col-gutter-x-sm q-mt-sm">
            <div class="col text-h4">
              {{ getPositionPath(item) }}
            </div>
            <div class="col-auto text-h3 text-right">
              {{ item.selected }}
            </div>
          </div>
          </template>
        </template>
      </q-scroll-area>


    <q-icon name="mdi-arrow-down-thin" size="lg" class="q-mt-md"/>

    <div class="text-h3 q-mt-md q-mb-xl">
      OUT
    </div>

    <q-space></q-space>
    <div class="row q-col-gutter-x-sm">
      <div class="col-6">
        <q-btn
          color="theme-grey"
          class="full-width"
          :label="$t('back')"
          @click="back"
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
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useShipmentStore } from '@/stores/shipment';

const router = useRouter();
const shipment = useShipmentStore();

const serialItems = computed(() =>
  shipment.selectedInventory
    .filter(item => shipment.inventory.find(i => i._key === item._key)?.serial_key)
    .map(item => {
      const inventoryItem = shipment.inventory.find(i => i._key === item._key);
      return {
        _key: item._key,
        serial_code: inventoryItem.serial_code,
        path: inventoryItem.path
      };
    })
);

const nonSerialItems = computed(() =>
  shipment.selectedInventory.filter(item =>
    !shipment.inventory.find(i => i._key === item._key)?.serial_key &&
    item.selected > 0
  )
);

const totalQuantity = computed(() => {
  return shipment.selectedInventory.reduce((total, item) => total + item.selected, 0);
});

function getPositionPath(item) {
  const inventoryItem = shipment.inventory.find(i => i._key === item._key);
  if (!inventoryItem) {
    return '';
  }
  return inventoryItem.path.map(p => p.position_code).join(' → ');
}

function back() {
  shipment.stage = 'inventory';
}

async function confirm() {
  const success = await shipment.confirmShipment();
  if (success) {
    shipment.$reset();
    router.push({ name: 'ShipmentRoot' });
  }
}
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
