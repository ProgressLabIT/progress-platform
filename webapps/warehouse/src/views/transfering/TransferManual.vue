<template>
  <q-page class="q-px-md q-pt-lg column fit q-col-gutter-y-lg">

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

<!--
    <q-btn-toggle
      v-model="startFrom"
      @update:model-value="reset"
      spread
      unelevated
      toggle-color="theme-blue"
      color="blue-backdrop"
      :options="[
        { label: $t('position'), value: 'position' },
        { label: $t('serial'), value: 'serial' },
      ]"
    />

      <SearchOrScan
      v-model="filter"
      @update:model-value="search"
    />

    <template v-if="results.length === 0">
      <q-space />
      <div v-if="filter.length === 0" class="col-auto q-mb-sm text-h1 item-center" style="width: 70%;">
        {{  $t('scan_start_position_or_serial') }}
      </div>
      <div  v-else class="col-auto q-mb-sm text-h1 item-center" style="width: 70%;">
        {{  $t('no_results') }}
      </div>
    </template>

    <template v-else>

      <div class="col-auto q-mb-sm text-h6">
        {{ $t(list_label) }} ({{ results.length }})
      </div>


      <div class="col scroll q-my-md column">
        <q-card
          v-for="item in results"
          :key="item.key"
          v-ripple
          bordered
          flat
          class="surface2 q-px-md q-py-md q-mb-sm"
          @click="selectItem(item)"
        >
          <div v-if="startFrom === 'serial'">
            <div class="text-h6 text-low">{{ item.product.code }}</div>
            <div class="text-body1 highlight">{{ item.code }}</div>
          </div>

          <div v-else>
            <div class="text-body1 highlight">{{ item.code }}</div>
          </div>
        </q-card>
      </div>

    </template>

    <q-space /> -->




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
