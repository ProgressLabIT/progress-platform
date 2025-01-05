<template>


    <!-- ITEM CODE & DESCRIPTION -->
    <div class="row">
      <div class="col-8">
        <div class="text-h6 q-mb-sm">
          {{ $t('product') }}
        </div>
        <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
          {{ lists.selectedItem.product_code }}
        </div>
        <div class="text-body2 smaller q-mt-xs ellipsis" style="max-width: 70vw;">
          {{ lists.selectedItem.product_description }}
        </div>
        <div
          v-if="lists.selectedItem.references.purchase_doc"
          class="text-h6 weight-bold uppercase q-mt-xs text-low">
          {{ lists.selectedItem.references.purchase_doc }}
        </div>
      </div>

      <div class="col column items-end">
        <div class="text-h6 q-mb-sm">{{ $t('quantity') }}</div>
        <div class="text-h3 q-pr-sm">
          {{ lists.movementQuantity }}
        </div>
      </div>


    </div>


    <div class="col-auto q-mt-lg">
      <div class="text-h3 q-mb-xs">
        {{ $t('destination') }}</div>
      <!-- POSITION SEARCH -->
      <SearchOrScan v-model="filter" dense @update:model-value="searchPositions" />
    </div>

    <!-- SELECTED POSITIONS -->
    <div class="col-auto q-mt-md">
      <div class="text-h6 q-mb-xs">POSIZIONI SELEZIONATE</div>
      <div class="row col-auto q-gutter-sm">
        <div
          v-for="selected in tempPositions"
          :key="selected._key"
          class="col-auto"
        >
          <q-card
            clickable
            flat
            class="bg-theme-blue q-pa-sm text-white weight-bold"
            @click="toggleSelection(selected)"
          >
            {{ selected.code }}
          </q-card>
        </div>
      </div>
    </div>

    <!-- AVAILABLE POSITIONS -->
    <div class="col q-mt-lg column">
      <div class="text-h6 q-mb-sm">POSIZIONI {{ positionResultsType }}</div>
      <q-scroll-area class="col q-pb-md">
        <div class="row q-gutter-sm">
          <div v-for="pos in availablePositions" :key="pos._key" class="col-auto">
            <q-card flat clickable bordered class="q-pa-sm" @click="toggleSelection(pos)">
              {{ pos.code }}
            </q-card>
          </div>
        </div>
      </q-scroll-area>
    </div>

    <q-space></q-space>
    <div class="col-auto">
      <q-btn
        color="theme-blue"
        :label="$t('position_create')"
        :disable="maxNewPositions <= 0"
        class="full-width"
        @click="openCreateContainerForm"
      />
    </div>


    <SlideUpCard
      v-model="showCreateContainerBottomSheet"
    >
      <CreateContainerForm
        :max="maxNewPositions"
        @hide="showCreateContainerBottomSheet=false"
        @select="selectNewContainers"
      />
    </SlideUpCard>

</template>

<script setup>
import { useListsStore } from 'stores/lists';
import SlideUpCard from '../SlideUpCard.vue';
import SearchOrScan from '../SearchOrScan.vue';
import { computed, ref } from 'vue';
import CreateContainerForm from '@/components/CreateContainerForm.vue';
import { api } from 'app/src/boot/axios';
import { Notify } from 'quasar';
const lists = useListsStore();
const positionResultsType = ref('RECENTI');
const positionResults = ref([]);

// const position = defineModel();



const filter = ref('');
const last_research = ref('');

const $emit = defineEmits(['next']);
const showCreateContainerBottomSheet = ref(false);
const tempPositions = defineModel();
const tempPositionsKeys = computed(() => tempPositions.value.map((p) => p._key));
const availablePositions = computed(() => {
  return positionResults.value.filter(
    (p) => !tempPositionsKeys.value.includes(p._key)
  );
});

const maxNewPositions = computed(() => {
  if (lists.selectedItem.type === 'serial') {
    return 1 - tempPositions.value.length;
  }
  else {
    return lists.movementQuantity - tempPositions.value.length;
  }
});

function loadPositions() {
  let params = {};

  if (filter.value) {
    params.search = filter.value;
    last_research.value = filter.value;
  }
  params.limit = 100;

  api.get('position', { params }).then((resp) => {
    positionResults.value = [...resp.data];
  });
}

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
  api.get('movement/latest-positions', { params: {
    limit: 5,
    movement_type: 'receipt',
    position_type: 'to'
  } }).then((resp) => {
    positionResults.value = resp.data;
  });
}


function openCreateContainerForm() {
  showCreateContainerBottomSheet.value = true;
}

function toggleSelection(position) {
  const index = tempPositionsKeys.value.findIndex((el) => el === position._key);
  if (index >= 0) {
    tempPositions.value.splice(index, 1);
  } else if (tempPositions.value.length >= lists.movementQuantity) {
    Notify.create({
      message: 'Non puoi selezionare più posizioni di quelle richieste',
      color: 'theme-orange',
      position: 'top',
      timeout: 1500
    })
  } else {
    tempPositions.value.push(position);
    if (lists.selectedItem.type === 'serial') {
      // For simplicity in defining the destination position for multiple setials use just one position
      $emit('next');
    }
  }
  adjustQuantityPerPosition();
}

function adjustQuantityPerPosition() {
  if (tempPositions.value.length <= 0) {
    return;
  }
  let remainingQty = lists.movementQuantity;
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
  showCreateContainerBottomSheet.value = false;
}

loadLatestUsedPositions();
adjustQuantityPerPosition();


</script>
