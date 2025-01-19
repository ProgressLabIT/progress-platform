<template>
  <div v-if="loading">
    {{ $t('incoming.quantity.loading') }}
  </div>
  <div v-else class="col column">
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto">
      <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
      <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
        {{ incoming.product?.code }}
      </div>
      <div class="text-body2 smaller q-mt-xs">
        {{ incoming.product?.description }}
      </div>
    </div>

    <!-- QUANTITY -->
    <div class="col column q-my-lg">
      <QuantitySelector v-model="tempQuantity" :heading="$t('quantity')" show-buttons class="col"/>
    </div>

    <!-- NAVIGATION -->
    <q-space></q-space>
    <div class="col-auto">
      <div class="row full-width q-gutter-y-md">
        <q-btn
          color="theme-grey"
          label="INDIETRO"
          unelevated
          class="col"
          @click="back"
        />
        <div class="q-mx-xs"></div>
        <q-btn
          color="theme-blue"
          unelevated
          label="AVANTI"
          class="col"
          :disable="tempQuantity <= 0"
          @click="selectQuantity(tempQuantity)"
        />
        <q-btn
          color="theme-blue"
          :label="$t('print_label')"
          unelevated
          class="col-12"
          @click="printProductLabel(incoming.product.code, incoming.product.description)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import QuantitySelector from '@/components/QuantitySelector.vue';
import { useIncomingStore } from 'app/src/stores/incoming';
import { printProductLabel } from 'app/src/lib/print';

const incoming = useIncomingStore();

const loading = ref(false);
const tempQuantity = ref(incoming.quantity);
// const product_print_template = ref(undefined);


// function loadPrintTemplates() {
//   api
//     .get('print-template', {
//       params: { context: 'product', context_key: incoming.product._key },
//     })
//     .then((data) => {
//       if (data && data?.data?.length > 0) {
//         product_print_template.value = data.data;
//       } else {
//         product_print_template.value = undefined;
//       }
//     });
// }

function selectQuantity(quantity) {
  incoming.quantity = quantity;
  incoming.stage = 'position'
}

function back() {
  incoming.stage = 'product';
  incoming.quantity = 0
}

// onMounted(() => {
//   loadPrintTemplates();
// });
</script>
