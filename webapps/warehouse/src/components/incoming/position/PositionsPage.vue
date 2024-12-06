<template>
  <div class="col column full-width">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto column full-width">
      <div class="row">
        <div class="col">
          <div class="text-h6 q-mb-sm">PRODOTTO</div>
          <div class="text-h1 q-pr-sm" style="word-wrap: break-word">
            {{ incoming.product?.code }}
          </div>
        </div>
        <div class="col-auto">
          <div class="text-h6 text-right q-mb-sm">QUANTITÀ</div>
          <div class="text-h1 text-right">
            {{ incoming.quantity }}
          </div>
        </div>
      </div>
      <div class="text-body1 q-mt-xs">
        {{ incoming.product?.description }}
      </div>
    </div>

    <div class="text-h6 q-mb-md q-mt-md">DESTINAZIONE</div>
    <!-- POSITION SEARCH -->
    <SearchOrScan v-model="filter" @update:model-value="loadPositions" />

    <!-- SELECTED POSITIONS -->
    <div class="text-h6">POSIZIONI SELEZIONATE</div>
    <div class="row col-auto q-col-gutter-x-sm q-mt-md">
      <div
        v-for="selected in incoming.positions"
        :key="selected._key"
        class="col-auto"
      >
        <q-chip
          clickable
          color="theme-blue"
          size="lg"
          @click="toggleSelection(selected)"
        >
          {{ selected.code }}
        </q-chip>
      </div>
    </div>

    <!-- AVAILABLE POSITIONS -->
    <div class="q-mt-lg text-h6">POSIZIONI DISPONIBILI</div>
    <div class="col scroll">
      <div class="row full-width q-col-gutter-x-sm q-mt-md">
        <div v-for="pos in availablePositions" :key="pos._key" class="col-auto">
          <q-chip clickable outline size="lg" @click="toggleSelection(pos)">
            {{ pos.code }}
          </q-chip>
        </div>
      </div>
    </div>

    <q-space></q-space>

    <div class="col-auto q-gutter-y-md row justify-center">
      <!-- <q-btn
        color="theme-blue"
        :label="$t('incoming.positions.create_container')"
        class="col-12"
        size="xl"
      /> -->
      <q-btn
        color="theme-blue"
        label="INDIETRO"
        class="col"
        size="xl"
        @click="router.back()"
      />
      <div class="q-mx-xs"></div>
      <q-btn
        color="theme-blue"
        label="AVANTI"
        class="col"
        size="xl"
        @click="router.push({ name: 'IncomingConfirm' })"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { api } from 'app/src/boot/axios';
import { useIncomingStore } from 'app/src/stores/incoming';
import SearchOrScan from '../../SearchOrScan.vue';

const incoming = useIncomingStore();
const router = useRouter();

const loading = ref(false);

const filter = ref('');
const last_research = ref('');
const positionResults = ref([]);
const latest_used_positions = ref(undefined);

function loadLatestUsedPositions() {
  if (latest_used_positions.value) {
    positionResults.value = latest_used_positions.value;
  } else {
    loading.value = true;
    api.get('movement/latest-receipt-positions', { limit: 10 }).then((resp) => {
      latest_used_positions.value = resp.data;
      positionResults.value = latest_used_positions.value;
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
    positionResults.value = resp.data;
    loading.value = false;
  });
}

const availablePositions = computed(() => {
  return positionResults.value.filter(
    (p) => !incoming.positionKeys.includes(p._key)
  );
});

// function showCreateContainerBottomSheet() {
//   // this.$bus.emit('show-create-container');
// }

function toggleSelection(position) {
  console.log(position, incoming.positionKeys);
  const index = incoming.positionKeys.findIndex((el) => el === position._key);
  if (index >= 0) {
    incoming.positions.splice(index, 1);
  } else {
    incoming.positions.push(position);
  }
  adjustQuantityPerPosition();
}

function adjustQuantityPerPosition() {
  if (incoming.positions.length <= 0) {
    return;
  }
  let remainingQty = incoming.quantity;
  let remainingPos = incoming.positions.length;
  for (let position of incoming.positions) {
    let posQty = Math.floor(remainingQty / remainingPos);
    position.quantity = posQty;
    remainingPos--;
    remainingQty -= posQty;
  }
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
