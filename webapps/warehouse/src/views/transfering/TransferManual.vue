<template>
  <q-page class="q-px-md column fit">

    <template v-if="transfer.selectMode === undefined">
      <SlideUpCard
        :model-value="true"
        height="20vh"
        @hide="router.push({ name: 'TransferRoot'})"
      >
        <q-btn
          class="full-width col"
          :label="$t('start_from_serial')"
          color="primary"
          @click="transfer.selectMode = 'serials'"
        />
        <div class="q-my-sm"></div>
        <q-btn
          class="full-width col"
          :label="$t('start_from_position')"
          color="primary"
          @click="transfer.selectMode = 'position'"
        />
      </SlideUpCard>
    </template>

    <template v-else>
      <TransferManualFromPosition v-if="transfer.stage === 'start' && transfer.selectMode === 'position'" />
      <TransferManualSerials v-if="transfer.stage === 'start' && transfer.selectMode === 'serials'" />
      <TransferManualContents v-if="transfer.stage === 'contents' && transfer.selectMode === 'position'" />
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
import TransferManualContents from '@/components/transfer/TransferManualContents.vue';
import { useTransferStore } from '@/stores/transfer';
import SlideUpCard from '@/components/SlideUpCard.vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const transfer = useTransferStore();

onBeforeRouteLeave(() => {
  transfer.$reset();
});
</script>
