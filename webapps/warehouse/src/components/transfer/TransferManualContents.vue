<template>
  <div class="column col q-gutter-y-md full-width">

    <!-- Start position -->
    <div class="row items-center q-gutter-x-md">
      <div class="text-h6">
        {{ $t('transfer_from_position') }}
      </div>
      <q-chip color="theme-grey" class="text-body2">
        {{ transfer.startPosition.code }}
      </q-chip>
    </div>

    <!-- Contents search / selection -->
    <div class="text-h2">{{ $t('transfer_contents_select')}}</div>
    <SearchOrScan v-model="filter" @update:model-value="searchContents" />

    <template v-if="list.length === 0">
      <div class="text-body2">{{ $t('no_results')}}</div>
    </template>

    <q-scroll-area v-else class="col scroll">
      <q-list>
        <q-item
          v-for="item in list"
          :key="item._key"
          clickable
          class="content-card q-my-xs q-pa-md text-body1"
          :class="getColor(item)"
          @click="toggleItem(item)"
        >
          <q-item-section avatar>
            <q-icon :name="contentIcon[item.type]" />
          </q-item-section>
          <q-item-section>
              <div v-if="item.type === 'serial'" class="text-h6">{{ item.product_code }}</div>
              <div class="highlight">{{ item.code }}</div>
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


    <q-space></q-space>

    <q-btn :disable="transfer.contents.length === 0" color="theme-blue" :label="$t('next')" @click="next" />
    <q-btn color="theme-grey" :label="$t('cancel')" @click="cancel" />

    <SlideUpCard
      :model-value="cardItem !== null"
      @hide="cardItem = null"
    >
      <!-- Transfer container or use as start position  -->
      <TransferManualPositionAction
        v-if="cardItem.type === 'position'"
        :position="cardItem"
        @select-contents="changeStartPosition"
        @select-container="transferContainer(cardItem)"
      />
      <!-- Select product quantity -->
      <template v-else>
        <div class="text-h2">{{ $t('quantity') }} {{ cardItem.code }}</div>
        <QuantitySelector v-model="itemQuantity" show-buttons selector-style="min-height: 100px;" min="1" :max="cardItem.quantity"/>
        <q-btn color="theme-blue" class="q-mt-md" :label="$t('transfer_quantity')" @click="selectItemQuantity" />
      </template>
    </SlideUpCard>

  </div>
</template>

<script setup>
import { ref } from 'vue';
import { api } from '@/boot/axios';
import { useTransferStore } from '@/stores/transfer';
import QuantitySelector from '@/components/QuantitySelector.vue';
import SearchOrScan from '@/components/SearchOrScan.vue';
import SlideUpCard from '@/components/SlideUpCard.vue';
import TransferManualPositionAction from '@/components/transfer/TransferManualPositionAction.vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const transfer = useTransferStore();

const filter = ref('');
const results = ref([]);
const list = ref([]);
const cardItem = ref(null);
const itemQuantity = ref(1);

function getPositionContents(position, search = null) {
  api.get(`position/${position._key}`, { params: { search } }).then((resp) => {
    results.value = resp.data;
    list.value = resp.data;
  });
}

getPositionContents(transfer.startPosition);

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
  return transfer.contents.find(c => c._id === item._id) ? `bg-theme-${color}` : `bg-${color}-backdrop`
}

async function searchContents() {
  if (filter.value.length === 0) {
    list.value = results.value;
    return
  }
  api.get(`position/${transfer.startPosition._key}`, { params: { search: filter.value } }).then((resp) => {
    if (resp.data.length === 1 && resp.data[0].code === filter.value) {
      toggleItem(resp.data[0]);
      filter.value = null;
    }
    else {
      list.value = resp.data;
    }
  })
}

function toggleItem(item) {
  if (transfer.contents.find(c => c._id === item._id)) {
    transfer.contents = transfer.contents.filter(c => c._id !== item._id);
  } else {
    if (['position', 'product'].includes(item.type)) {
      cardItem.value = item;
    } else {
      transfer.contents.push(item);
    }
  }
}

function selectItemQuantity() {
  transfer.contents.push({
    ...cardItem.value,
    quantity: itemQuantity.value,
  });
  cardItem.value = null;
  itemQuantity.value = 1;
}

function getItemSelectedQty(item) {
  return transfer.contents.find(c => c._id === item._id)?.quantity || 0;
}

function changeStartPosition() {
  transfer.startPosition = cardItem.value;
  transfer.contents = [];
  getPositionContents(cardItem.value);
  cardItem.value = null;
}

function transferContainer(item) {
  transfer.contents.push(item);
  cardItem.value = null;
}

function next() {
  transfer.stage = 'destination';
}

function cancel() {
  transfer.$reset()
  router.push({ name: 'TransferRoot'})
}

</script>

<style scoped lang="sass">
.content-card
  border-radius: 5px
</style>
