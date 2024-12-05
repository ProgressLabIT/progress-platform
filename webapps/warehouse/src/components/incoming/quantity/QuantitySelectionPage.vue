<template>
  <div v-if="loading">
    {{ $t('incoming.quantity.loading') }}
  </div>
  <div v-else class="col column q-mt-xl q-pb-md">

    <!-- ITEM CODE & DESCRIPTION -->
    <div class="col-auto">
      <div class="text-h6 q-mb-sm">
        PRODOTTO
      </div>
      <div class="text-h1 q-pr-sm" style="word-wrap: break-word;">
        {{ incoming.product?.code }}
      </div>
      <div class="text-body1 q-mt-xs">
        {{ incoming.product?.description }}
      </div>
    </div>

    <!-- QUANTITY -->
    <div class="col-4 q-mt-xl">
      <div class="text-h6 q-mb-md">
        QUANTITÀ
      </div>

      <QuantitySelector v-model="incoming.quantity" />

      <!-- ±10/100 -->
      <div class="full-width row q-mt-md">
        <div class="col">
          <q-btn
            color="theme-blue"
            outline
            label="-10"
            size="lg"
            class="full-width"
            @click="updateQuantity(-10)"
          />
        </div>
        <div class="q-mx-xs"></div>
        <div class="col">
          <q-btn
            color="theme-blue"
            outline
            label="+10"
            size="lg"
            class="full-width"
            @click="updateQuantity(10)"
          />
        </div>
      </div>
      <div class="full-width row q-mt-md">
        <div class="col">
          <q-btn
            color="theme-blue"
            outline
            label="-100"
            size="lg"
            class="full-width"
            @click="updateQuantity(-100)"
          />
        </div>
        <div class="q-mx-xs"></div>
        <div class="col">
          <q-btn
            color="theme-blue"
            outline
            label="+100"
            size="lg"
            class="full-width"
            @click="updateQuantity(100)"
          />
        </div>
      </div>
    </div>

    <!-- NAVIGATION -->
    <q-space></q-space>
    <div class="col-auto">
      <div class="row full-width q-gutter-y-md">
        <q-btn
          color="theme-grey"
          :label="$t('back')"
          unelevated
          size="xl"
          class="col"
          @click="router.back()"
        />
        <div class="q-mx-xs"></div>
        <q-btn
          color="theme-blue"
          unelevated
          :label="$t('next')"
          size="xl"
          class="col"
          @click="router.push({ name: 'IncomingPosition' })"
        />
        <q-btn
          color="theme-blue"
          :label="$t('incoming.quantity.print_label')"
          unelevated
          class="col-12"
          size="xl"
          @click="showPrintLabelBottomSheet"
        />
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useIncomingStore } from 'app/src/stores/incoming';
import { useRouter } from 'vue-router';
import QuantitySelector from '@/components/QuantitySelector.vue';

const incoming = useIncomingStore()

const router = useRouter()

const loading = ref(false)

  // data() {
  //   return {
  //     show_print_label: false,
  //     print_templates: undefined,
  //     selected_templates: undefined,
  //     loading: true,
  //   };
  // },

function updateQuantity(howMuch) {
  incoming.quantity = Math.max(0, incoming.quantity + howMuch)
}

function showPrintLabelBottomSheet() {

};
</script>
