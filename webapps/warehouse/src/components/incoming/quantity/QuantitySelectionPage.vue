<template>
  <div v-if="loading">
    {{ $t('incoming.quantity.loading') }}
  </div>
  <div v-else class="col column q-pb-md">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto">
      <div class="text-h6 q-mb-sm">PRODOTTO</div>
      <div class="text-h1 q-pr-sm" style="word-wrap: break-word">
        {{ incoming.product?.code }}
      </div>
      <div class="text-body1 q-mt-xs">
        {{ incoming.product?.description }}
      </div>
    </div>

    <!-- QUANTITY -->
    <div class="col column q-my-xl">
      <div class="text-h6 col-auto q-mb-md">QUANTITÀ</div>

      <QuantitySelector v-model="tempQuantity" class="col"/>


    </div>

    <!-- NAVIGATION -->
    <q-space></q-space>
    <div class="col-auto">
      <div class="row full-width q-gutter-y-md">
        <q-btn
          color="theme-grey"
          label="INDIETRO"
          unelevated
          size="xl"
          class="col"
          @click="back"
        />
        <div class="q-mx-xs"></div>
        <q-btn
          color="theme-blue"
          unelevated
          label="AVANTI"
          size="xl"
          class="col"
          :disable="tempQuantity <= 0"
          @click="selectQuantity(tempQuantity)"
        />
        <q-btn
          :disable="!product_print_template"
          color="theme-blue"
          :label="$t('print_label')"
          unelevated
          class="col-12"
          size="xl"
          @click="printProductLabel"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
//import { generateProductLabel, print } from 'app/src/lib/zebraTemplates';
import { onMounted, ref } from 'vue';
import QuantitySelector from '@/components/QuantitySelector.vue';
import { api } from 'app/src/boot/axios';
import { useIncomingStore } from 'app/src/stores/incoming';

const incoming = useIncomingStore();

const loading = ref(false);
const tempQuantity = ref(incoming.quantity);
const product_print_template = ref(undefined);

function printProductLabel() {
  //const template = generateProductLabel(
  //  incoming.product.code,
  //  incoming.product.description
  //);
  //print(template);
}

function loadPrintTemplates() {
  api
    .get('print-template', {
      params: { context: 'product', context_key: incoming.product._key },
    })
    .then((data) => {
      if (data && data?.data?.length > 0) {
        product_print_template.value = data.data;
      } else {
        product_print_template.value = undefined;
      }
    });
}

function selectQuantity(quantity) {
  incoming.quantity = quantity;
  incoming.stage = 'position'
}

function back() {
  incoming.stage = 'product';
  incoming.quantity = 0
}

onMounted(() => {
  loadPrintTemplates();
});
</script>
