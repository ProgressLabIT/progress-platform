<template>
  <div class="col column">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto column full-width">
      <div class="row">
        <div class="col">
          <div class="text-h6 text-low weight-bold text-uppercase q-mb-xs">
            {{ $t('product')}}
          </div>
          <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
            {{ incoming.product?.code }}
          </div>
        </div>
        <div class="col-auto">
          <div class="text-h6 text-right q-mb-xs">{{ $t('quantity') }}</div>
          <div class="text-h3 text-right">
            {{ incoming.refQuantity }}
          </div>
        </div>
      </div>
    </div>

    <div class="col-auto q-mt-md">
      <div class="text-h3 q-mb-xs">
        {{ $t('destination') }}</div>
      <!-- POSITION SEARCH -->
      <SearchOrScan v-model="filter" @update:model-value="searchPositions" />
    </div>

    <!-- SELECTED POSITIONS -->
    <div class="col-auto q-mt-md">
      <div class="text-h6 q-mb-sm">POSIZIONI SELEZIONATE</div>
      <div class="row col-auto q-col-gutter-sm">
        <div
          v-for="selected in tempPositions"
          :key="selected._key"
          class="col-auto"
        >
          <q-card
            flat
            class="q-pa-sm bg-theme-green highlight text-body2"
            @click="toggleSelection(selected)"
          >
            {{ selected.code }}
          </q-card>
        </div>
      </div>
    </div>

    <!-- AVAILABLE POSITIONS -->
    <div class="text-h6 col-auto q-mt-lg">POSIZIONI {{ positionResultsType }}</div>
    <q-scroll-area class="col q-mt-md">
      <div class="row q-col-gutter-sm">
        <div
          v-for="pos in availablePositions"
          :key="pos._key"
          class="col-auto"
        >
          <q-card
            flat
            bordered
            class="q-pa-sm transparent text-body2"
            @click="toggleSelection(pos)"
          >
            {{ pos.code }}
          </q-card>
        </div>
      </div>
    </q-scroll-area>
    <!-- <q-space></q-space> -->
    <div class="col-auto q-gutter-y-sm row justify-center q-mt-md">
      <q-btn
        outline
        color="theme-blue"
        :label="$t('select_root_position')"
        class="col"
        @click="selectRootPosition"
      />
      <q-btn
        color="theme-blue"
        :label="$t('position_create')"
        :disable="tempPositions.length >= incoming.refQuantity"
        class="col-12"
        @click="openCreateContainerForm"
      />
      <q-btn
        color="theme-grey"
        :label="$t('back')"
        class="col"
        @click="back"
      />
      <div class="q-mx-xs"></div>
      <q-btn
        :disable="tempPositions.length === 0"
        color="theme-blue"
        :label="$t('next')"
        class="col"
        @click="next"
      />
    </div>

    <SlideUpCard
      v-model="showCreateContainerBottomSheet"
    >
      <CreateContainerForm
        :max="incoming.refQuantity - tempPositions.length"
        @hide="showCreateContainerBottomSheet=false"
        @select="selectNewContainers"
      />
    </SlideUpCard>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import CreateContainerForm from '@/components/CreateContainerForm.vue';
import SearchOrScan from '@/components/SearchOrScan.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';
import { api } from 'app/src/boot/axios';
import { useIncomingStore } from 'app/src/stores/incoming';
import { Notify } from 'quasar';
const { t: $t } = useI18n();
const incoming = useIncomingStore();

const loading = ref(false);

const filter = ref('');
const last_research = ref('');
const positionResults = ref([]);
const positionResultsType = ref('RECENTI');
const showCreateContainerBottomSheet = ref(false);

const tempPositions = ref([]);
const tempPositionsKeys = computed(() => tempPositions.value.map((p) => p._key));



function searchPositions() {
  if (filter.value !== last_research.value) {
    if (filter.value === '') {
      loadLatestUsedPositions();
      positionResultsType.value = 'RECENTI'
    } else {
      loadPositions(filter);
      positionResultsType.value = 'DISPONIBILI'
    }
  }
}


function loadLatestUsedPositions() {
  if (incoming.recentPositions.length) {
    positionResults.value = incoming.recentPositions;
  }
  else {
    loading.value = true;
    api.get('movement/latest-positions', { params: {
      position_type: 'to',
      movement_type: 'receipt',
      limit: 10
    }}).then((resp) => {
      incoming.recentPositions = resp.data;
      positionResults.value = incoming.recentPositions;
      loading.value = false;
    });
  }
}

function loadPositions() {
  loading.value = true;
  let params = {};

  if (filter.value) {
    params.search = filter.value;
    last_research.value = filter.value;
  }
  params.limit = 100;

  api.get('position', { params }).then((resp) => {
    positionResults.value = [...resp.data];
    loading.value = false;
  });
}

const availablePositions = computed(() => {
  return positionResults.value.filter(
    (p) => !tempPositionsKeys.value.includes(p._key)
  );
});

function openCreateContainerForm() {
  showCreateContainerBottomSheet.value = true;
}

function toggleSelection(position) {
  const index = tempPositionsKeys.value.findIndex((el) => el === position._key);
  if (index >= 0) {
    tempPositions.value.splice(index, 1);
  } else if (tempPositions.value.length >= incoming.refQuantity) {
    Notify.create({
      message: 'Non puoi selezionare più posizioni di quelle richieste',
      color: 'theme-orange',
      position: 'top',
      timeout: 1500
    })
  } else {
    tempPositions.value.push(position);
    if (incoming.product.traceability_level) {
      // For simplicity in defining the destination position for multiple setials use just one position
      next()
    }
  }
}

function adjustQuantityPerPosition() {
  if (tempPositions.value.length <= 0) {
    return;
  }
  let remainingQty = incoming.refQuantity;
  let remainingPos = tempPositions.value.length;
  for (let position of tempPositions.value) {
    let posQty = Math.floor(remainingQty / remainingPos);
    position.quantity = posQty;
    remainingPos--;
    remainingQty -= posQty;
  }
}

function selectNewContainers(containers) {
  tempPositions.value = [...tempPositions.value, ...containers];
  next();
}

function selectRootPosition() {
  incoming.positions = [{_key: 'IN', code: 'IN', quantity: incoming.refQuantity}];
  incoming.stage = 'confirm';
}

function next() {
  adjustQuantityPerPosition()
  incoming.positions = [...tempPositions.value];
  incoming.stage = 'confirm';
}

function back() {
  incoming.stage = incoming.product.traceability_level ? 'serials' : 'quantity';
}

onMounted(() => {
  loadLatestUsedPositions();
  adjustQuantityPerPosition();
});
</script>

<style lang="sass">
.grid-style-transition
  transition: transform .28s, background-color .28s
</style>
