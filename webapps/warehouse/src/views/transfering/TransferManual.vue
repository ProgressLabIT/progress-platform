<template>
  <q-page class="q-px-md column fit">

    <template v-if="transfer.selectMode === undefined">
      <SlideUpCard
        :model-value="true"
        @hide="router.push({ name: 'TransferRoot'})"
      >
        <div class="column full-height q-gutter-y-md">
          <div class="text-h3">
            Da dove vuoi iniziare?
          </div>
          <q-btn
            class="full-width"
            :label="$t('product')"
            color="theme-blue"
            @click="transfer.selectMode = 'product'"
          />
          <q-btn
            class="full-width"
            :label="$t('serial', 2)"
            color="theme-green"
            @click="transfer.selectMode = 'serials'"
          />
          <q-btn
            class="full-width"
            :label="$t('position')"
            color="theme-grey"
            @click="transfer.selectMode = 'position'"
          />
        </div>
      </SlideUpCard>
    </template>

    <template v-else>
      <template v-if="transfer.stage === 'start'">
        <ProductSearch v-if="transfer.selectMode === 'product'" @select="selectProduct" />
        <TransferManualSerials v-if="transfer.selectMode === 'serials'" />
        <TransferManualFromPosition v-if="transfer.selectMode === 'position'" />
      </template>

      <template v-if="transfer.stage === 'contents'">
        <TransferManualProductInventory v-if="transfer.selectMode === 'product'" />
        <TransferManualPositionContents v-if="transfer.selectMode === 'position'" />
      </template>

      <!-- Destination -->
      <TransferManualDestination v-if="transfer.stage === 'destination'"/>
      <TransferManualConfirm v-if="transfer.stage === 'confirm'"/>
    </template>

  </q-page>
</template>

<script setup>
import { onBeforeRouteLeave } from 'vue-router';
import TransferManualFromPosition from '@/components/transfer/TransferManualFromPosition.vue';
import TransferManualSerials from '@/components/transfer/TransferManualSerials.vue';
import TransferManualDestination from '@/components/transfer/TransferManualDestination.vue';
import TransferManualConfirm from '@/components/transfer/TransferManualConfirm.vue';
import TransferManualProductInventory from '@/components/transfer/TransferManualProductInventory.vue';
import TransferManualPositionContents from '@/components/transfer/TransferManualPositionContents.vue';
import { useTransferStore } from '@/stores/transfer';
import SlideUpCard from '@/components/SlideUpCard.vue';
import { useRouter } from 'vue-router';
import ProductSearch from 'app/src/components/ProductSearch.vue';

const router = useRouter();

const transfer = useTransferStore();

const selectProduct = (product) => {
  transfer.product = product;
  transfer.stage = 'contents';
};

onBeforeRouteLeave(() => {
  transfer.$reset();
});
</script>
