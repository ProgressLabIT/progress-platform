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
    <div class="row items-center q-gutter-x-xs">
      <div class="text-h2">{{ $t('transfer_contents_select')}}</div>
      <q-space></q-space>
      <q-btn color="theme-grey" size="xs" padding="xs md" icon="mdi-checkbox-multiple-blank-outline" @click="() => toggleAll(false)" />
      <q-btn color="theme-blue" size="xs" padding="xs md" icon="mdi-checkbox-multiple-marked" @click="() => toggleAll(true)" />
    </div>
    <SearchOrScan v-model="filter" @update:model-value="searchContents" />

    <template v-if="list.length === 0">
      <div class="text-body2">{{ $t('no_results')}}</div>
    </template>

    <q-virtual-scroll
      v-else
      :items="list"
      v-slot="{ item }"
      class="col"
    >
      <q-item
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
    </q-virtual-scroll>



    <q-btn :disable="transfer.contents.length === 0" color="theme-blue" :label="$t('next')" @click="next" />
    <q-btn color="theme-grey" :label="$t('cancel')" @click="cancel" />

    <SlideUpCard
      :model-value="cardItem !== null"
      @hide="cardItem = null"
    >
      <!-- Transfer container or use as start position  -->
      <PositionAction
        v-if="cardItem.type === 'position'"
        :position="cardItem"
        @select-contents="changeStartPosition"
        @select-container="transferContainer"
      />
      <!-- Select product quantity -->
      <template v-else>
        <QuantitySelector
          v-model="itemQuantity"
          show-buttons
          selector-style="min-height: 100px;"
          min="1"
          :max="cardItem.quantity"
          :heading="$t('quantity') + ' ' + cardItem.code"
        />
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
import PositionAction from '@/components/PositionAction.vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const transfer = useTransferStore();

const filter = ref('');
const results = ref([]);
const list = ref([]);
const cardItem = ref(null);
const itemQuantity = ref(1);

function getPositionContents(position_key, search = null) {
  api.get(`position/${position_key}`, { params: { search } }).then((resp) => {
    // Extract contents from object response format: { position, path, contents }
    const contents = resp.data?.contents || [];
    results.value = contents;
    list.value = contents;
  });
}

getPositionContents(transfer.startPosition._key);

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
  return transfer.contents.find(c => c._key === item._key) ? `bg-theme-${color}` : `bg-${color}-backdrop`
}

async function searchContents() {
  if (filter.value.length === 0) {
    list.value = results.value;
    return
  }
  api.get(`position/${transfer.startPosition._key}`, { params: { search: filter.value } }).then((resp) => {
    // Extract contents from object response format: { position, path, contents }
    const contents = resp.data?.contents || [];
    if (contents.length === 1 && contents[0].code === filter.value) {
      toggleItem(contents[0]);
      filter.value = null;
    }
    else {
      list.value = contents;
    }
  })
}

function toggleItem(item) {
  // if item is already in contents, remove it
  if (transfer.contents.find(c => c._key === item._key)) {
    transfer.contents = transfer.contents.filter(c => c._key !== item._key);
  } else {
    switch (item.type) {
      case 'position':
        if (item.position_fixed) {
          cardItem.value = item;
          changeStartPosition();
        }
        else {
          cardItem.value = item;
        }
        break;
      case 'product':
        cardItem.value = item;
        break;
      case 'serial':
        transfer.contents.push(item);
        break;
      default:
        break;
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
  return transfer.contents.find(c => c._key === item._key)?.quantity || 0;
}

function changeStartPosition() {
  // Card has been populated with inventory record: the _key of the new start position is NOT the _key of the inventory record
  transfer.startPosition = { _key: cardItem.value.position_key, code: cardItem.value.code };
  transfer.contents = [];
  getPositionContents(cardItem.value.position_key);
  cardItem.value = null;
  filter.value = null;
}

function transferContainer() {
  transfer.contents.push({
    ...cardItem.value,
    type: 'position',
    position_key: cardItem.value.position_key,
  });
  cardItem.value = null;
}

function toggleAll(select = true) {
  if (select) {
    // Add all items that aren't already in contents, excluding fixed positions
    list.value.filter(item => !item.position_fixed).forEach(item => {
      if (!transfer.contents.find(c => c._key === item._key)) {
        // if (['position', 'product'].includes(item.type)) {
        //   // Skip positions/products as they need quantity input
        //   return;
        // }
        transfer.contents.push(item);
      }
    });
  } else {
    // Remove all items from current list
    transfer.contents = transfer.contents.filter(
      content => !list.value.find(item => item._key === content._key)
    );
  }
}


function next() {
  transfer.stage = 'destination';
}

function cancel() {
  transfer.$reset()
  router.push({ name: 'TransferRoot'})
}

</script>

<style lang="sass">
.content-card
  border-radius: 5px
</style>
