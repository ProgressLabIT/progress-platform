<template>
  <div class="col column full-width">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto column full-width">
      <div class="row">
        <div class="col">
          <div class="text-h6 q-mb-sm text-low weight-bold text-uppercase">{{ $t('product')}}</div>
          <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
            {{ incoming.product?.code }}
          </div>
        </div>
        <div class="col-auto">
          <div class="text-h6 text-right q-mb-sm">{{ $t('quantity') }}</div>
          <div class="text-h3 text-right">
            {{ incoming.quantity }}
          </div>
        </div>
      </div>
    </div>

    <div class="text-h3 q-mb-md q-mt-md">{{ $t('destination') }}</div>
    <!-- POSITION SEARCH -->
    <SearchOrScan v-model="filter" @update:model-value="searchPositions" />

    <!-- SELECTED POSITIONS -->
    <div class="text-h6">POSIZIONI SELEZIONATE</div>
    <div class="row col-auto q-col-gutter-x-sm q-mt-md">
      <div
        v-for="selected in tempPositions"
        :key="selected._key"
        class="col-auto"
      >
        <q-chip
          clickable
          color="theme-blue"
          class="text-body1"
          @click="toggleSelection(selected)"
        >
          {{ selected.code }}
        </q-chip>
      </div>
    </div>

    <!-- AVAILABLE POSITIONS -->
    <div class="q-mt-lg text-h6">POSIZIONI {{ positionResultsType }}</div>
    <div class="col scroll">
      <div class="row full-width q-col-gutter-x-sm q-mt-md">
        <div v-for="pos in availablePositions" :key="pos._key" class="col-auto">
          <q-chip clickable outline class="text-body1" @click="toggleSelection(pos)">
            {{ pos.code }}
          </q-chip>
        </div>
      </div>
    </div>

    <q-space></q-space>

    <div class="col-auto q-gutter-y-md row justify-center">
      <q-btn
        color="theme-blue"
        :label="$t('position_create')"
        :disable="tempPositions.length >= incoming.quantity"
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
        :max="incoming.quantity - tempPositions.length"
        @hide="showCreateContainerBottomSheet=false"
        @select="selectNewContainers"
      />
    </SlideUpCard>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { api } from 'app/src/boot/axios';
import { useIncomingStore } from 'app/src/stores/incoming';
import SearchOrScan from '@/components/SearchOrScan.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';
import CreateContainerForm from '@/components/CreateContainerForm.vue';
import { useI18n } from 'vue-i18n';

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
    api.get('movement/latest-positions', { limit: 10 }).then((resp) => {
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
  console.log('openCreateContainerForm');
  showCreateContainerBottomSheet.value = true;
}

function toggleSelection(position) {
  console.log(position, tempPositionsKeys.value);
  const index = tempPositionsKeys.value.findIndex((el) => el === position._key);
  if (index >= 0) {
    tempPositions.value.splice(index, 1);
  } else {
    tempPositions.value.push(position);
  }
}

function adjustQuantityPerPosition() {
  if (tempPositions.value.length <= 0) {
    return;
  }
  let remainingQty = incoming.quantity;
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

function next() {
  adjustQuantityPerPosition()
  incoming.positions = [...tempPositions.value];
  incoming.stage = 'confirm';
}

function back() {
  incoming.stage = 'quantity';
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
