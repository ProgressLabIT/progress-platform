<template>
  <div class="col column full-width q-pb-md">


    <!-- POSITION SELECTION -->
    <template v-if="stage === 'position'">
      <div class="text-h3 q-mb-md">{{ $t('start_from_position') }}</div>
      <SearchOrScan v-model="filter" @update:model-value="searchPositions" />

      <!-- NO RESULTS -->
      <template v-if="positionResults.length === 0">
        <div class="text-h2">{{ $t('no_results') }}</div>
      </template>

      <!-- AVAILABLE POSITIONS -->
      <template v-else>
        <div class="q-mt-lg text-h6">POSIZIONI {{ positionResultsType }}</div>
        <div class="col scroll q-my-md">
          <div class="row q-col-gutter-sm">
            <div v-for="pos in positionResults" :key="pos._key" class="col-auto">
              <q-card flat clickable bordered class="q-pa-sm transparent" @click="selectPosition(pos)">
                {{ pos.code }}
              </q-card>
            </div>
          </div>
        </div>
      </template>

      <q-space></q-space>

      <!-- ACTIONS -->
      <q-btn
        color="primary"
        outline
        :label="$t('select_root_position')"
        @click="selectRootPosition()"
      />
      <div class="q-my-sm"></div>
      <q-btn
        color="theme-grey"
        :label="$t('cancel')"
        class="full-width"
        @click="router.push({ name: 'InventoryRoot'})"
      />
      <div class="q-mx-xs"></div>
    </template>


    <!-- CONTENTS -->
    <template v-if="stage === 'contents'">
      <div class="row items-center q-mb-sm q-gutter-x-md">
        <div class="text-h3">{{ $t('position') }}</div>
        <q-chip class="highlight text-body2" color="theme-grey">{{ selectedPosition.code }}</q-chip>
      </div>

      <SearchOrScan
        v-model="filter"
        @update:model-value="loadPositionContents(selectedPosition._key)"
        class="q-mb-md"
      />

      <div class="text-h6" v-if="positionContents.length === 0">{{ $t('no_contents') }}</div>

      <template v-else>
        <div class="text-h6 q-mb-md">{{ $t('contents') }}</div>
        <q-virtual-scroll
          :items="positionContents"
          v-slot="{ item }"
          class="col q-mb-md"
        >
          <q-item
            :key="item._key"
            :clickable="item.type !== 'serial'"
            class="content-card q-my-xs q-pa-md text-body1"
            :class="getColor(item)"
            @click="selectItem(item)"
          >
            <q-item-section side>
              <q-icon :name="contentIcon[item.type]" />
            </q-item-section>
            <q-item-section>
                <div v-if="item.type === 'serial'" class="text-h6">{{ item.product_code }}</div>
                <div class="highlight">{{ item.code }}</div>
            </q-item-section>
            <q-item-section v-if="item.type === 'product'" side>
              <div class="text-body2">
                {{ item.quantity }}
              </div>
            </q-item-section>
          </q-item>
        </q-virtual-scroll>
      </template>

      <q-space></q-space>
      <q-btn
        color="theme-grey"
        :label="$t('back')"
        class="full-width"
        @click="backToPositionSelection()"
      />
    </template>

    <SlideUpCard :model-value="showAdjustQuantityCard" @hide="unselectItem()" height="400px">
      <QuantitySelector v-model="itemQuantity" show-buttons>
        <template #heading>
            <div class="col">
              <div class="text-h3">Modifica quantità</div>
              <div class="text-h3">{{ selectedItem.code }}</div>
            </div>
            <div class="col-auto highlight">
              <q-chip
                size="md"
                :color="adjustmentQuantity === 0 ? 'theme-grey' : (adjustmentQuantity > 0 ? 'theme-green' : 'theme-orange')"
                :label="(adjustmentQuantity > 0 ? '+' : '') + adjustmentQuantity"
                class="full-width"
                @click="selectedItem = null"
              />
            </div>
        </template>
      </QuantitySelector>
      <q-btn
        color="primary"
        :label="$t('confirm')"
        class="full-width q-mt-md"
        @click="confirmQuantity()"
      />
    </SlideUpCard>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';
import SearchOrScan from '@/components/SearchOrScan.vue';
import { useRouter } from 'vue-router';
import SlideUpCard from '@/components/SlideUpCard.vue';
import QuantitySelector from '@/components/QuantitySelector.vue';
import { sendEvent } from '@/composables/event';
import { timestamp } from '@/lib/TimeHandling';
import { Notify } from 'quasar';

const router = useRouter();
const { t: $t } = useI18n();

const loading = ref(false);
const stage = ref('position');
const filter = ref('');
const last_research = ref('');
const positionResults = ref([]);
const positionResultsType = ref('RECENTI');
const selectedPosition = ref(null);
const positionContents = ref([]);
const showAdjustQuantityCard = computed(() => selectedItem.value !== null);
const adjustmentQuantity = computed(() => itemQuantity.value - selectedItem.value.quantity);
const selectedItem = ref(null);
const itemQuantity = ref(0);

const contentIcon = {
  product: 'mdi-apps',
  serial: 'mdi-cube-scan',
  position: 'mdi-package-variant-closed',
}

function getColor(item) {
  const colorMap = {
    product: 'blue',
    serial: 'green',
    position: 'red'
  }
  const color = colorMap[item.type]
  return `bg-${color}-backdrop`
}


function loadLatestUsedPositions() {
  loading.value = true;
  api.get('movement/latest-positions', { params: {
    position_type: 'from',
    movement_type: 'transfer',
    limit: 10
  }})
  .then((resp) => {
    positionResults.value = resp.data;
    loading.value = false;
    positionResultsType.value = 'RECENTI';
  });
}

function searchPositions() {
  loading.value = true;
  let params = {};

  if (filter.value === last_research.value) {
    return
  }

  if (filter.value.length === 0) {
    loadLatestUsedPositions();
    positionResultsType.value = 'RECENTI'
  }

  else {
    params.search = filter.value;
    last_research.value = filter.value;
    params.limit = 100;

    api.get('position', { params }).then((resp) => {
      if (resp.data.length === 1 && resp.data[0].code === filter.value) {
        selectPosition(resp.data[0]);
      }
      else {
        positionResults.value = [...resp.data];
      }
      loading.value = false;
      positionResultsType.value = 'DISPONIBILI';
    });
  }
}

async function loadPositionContents(position_key) {
  const response = await api.get(`/position/${position_key}`, { params: { search: filter.value } });
  // Extract contents from object response format: { position, path, contents }
  positionContents.value = response.data?.contents || [];
}

function selectRootPosition() {
  selectPosition({
    fixed: true,
    _key: 'IN',
    code: 'IN',
  });
}

function selectPosition(position) {
  filter.value = '';
  selectedPosition.value = position;
  loadPositionContents(position._key);
  stage.value = 'contents';
}

function backToPositionSelection() {
  filter.value = '';
  selectedPosition.value = null;
  positionContents.value = [];
  stage.value = 'position';
}

onMounted(() => {
  loadLatestUsedPositions();
});

function selectItem(item) {
  if (item.type === 'position') {
    selectPosition({ _key: item.position_key, code: item.code });
  }
  else {
    adjustQuantity({ _key: item.product_key, code: item.product_code, quantity: item.quantity });
  }
}

function adjustQuantity(item) {
  itemQuantity.value = item.quantity;
  selectedItem.value = item;
}

function unselectItem() {
  selectedItem.value = null;
  itemQuantity.value = 0;
}

function confirmQuantity() {
  const now = timestamp();
  sendEvent({
    event_type: 'MOVEMENT_COMPLETED',
    event_data: {
      position_from: selectedPosition.value._key,
      position_to: selectedPosition.value._key,
      product_key: selectedItem.value._key,
      qt_planned: adjustmentQuantity.value,
      qt_confirmed: adjustmentQuantity.value,
      status: 'completed',
      movement_type: 'adjustment',
      start: now,
      end: now,
    }
  })
  .then(() => {
    loadPositionContents(selectedPosition.value._key);
    unselectItem();
    Notify.create({
      message: 'Quantità aggiornata',
      color: 'theme-green',
      position: 'top',
    });
  })
}



</script>

<style lang="sass">
.content-card
  border-radius: 5px

.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
