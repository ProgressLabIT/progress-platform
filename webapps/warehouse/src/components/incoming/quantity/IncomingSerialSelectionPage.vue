<template>
  <div class="col column q-gutter-y-sm">
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


    <div class="row items-center q-mt-lg">

      <div class="col-auto text-h3 q-mr-sm">
        Inserisci seriali
      </div>

      <q-chip v-if="incoming.serials.length" size="xs" color="theme-grey">
        <div class="smaller highlight">{{ incoming.serials.length }}</div>
      </q-chip>

    </div>

    <div class="col-auto row">
      <q-input
        filled
        for="serial-input"
        autofocus
        clearable
        class="col"
        input-class="text-uppercase"
        :model-value="newSerialCode"
        @update:model-value="(value) => newSerialCode = value.toUpperCase()"
        @keyup.enter="() => toggleItem(newSerialCode)"
      >
      </q-input>
      <q-btn
        color="theme-blue"
        unelevated
        padding="xs md"
        icon="mdi-plus"
        class="col-auto q-ml-md"
        :loading="loading"
        :disabled="newSerialCode.length === 0"
        @click="() => toggleItem(newSerialCode)"
      />
    </div>

    <q-scroll-area class="col">

      <div class="col-auto q-my-md row q-gutter-md">
        <q-card
          v-for="serialCode in incoming.serials"
          :key="serialCode"
          flat
          class="bg-theme-green q-pa-sm highlight"
          @click="toggleItem(serialCode)"
        >
          {{ serialCode }}
        </q-card>
      </div>

  </q-scroll-area>

    <q-btn
      :disable="incoming.serials.length === 0 || loading"
      color="theme-blue"
      :label="$t('next')"
      class="col-auto full-width"
      @click="next"
    />
    <q-btn
      color="grey"
      :label="$t('back')"
      class="col-auto full-width"
      :disable="loading"
      @click="back"
    />

  </div>
</template>

<script setup>
import { Notify } from 'quasar'
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';
import { useIncomingStore } from '@/stores/incoming';

const incoming = useIncomingStore();
const newSerialCode = ref('');
const loading = ref(false)
const { t: $t } = useI18n();


async function toggleItem(serialCode) {
  const index = incoming.serials.findIndex(i => i === serialCode);
  if (index !== -1) {
    // if item is already in the list, remove it
    incoming.serials.splice(index, 1)
    Notify.create({
      position: 'top',
      color: 'theme-grey',
      message: `Seriale ${serialCode} rimosso`,
      timeout: 1500
    })

  }
  else {
    loading.value = true;
    api.get('serial-code', { params: { product_key: incoming.product._key, serial_code: newSerialCode.value }}).then(({ data }) => {
      loading.value = false
      if (data.length > 0) {
        Notify.create({
          position: 'top',
          color: 'theme-orange',
          message: `Seriale ${serialCode} per il prodotto ${incoming.product.code} già esistente`,
          timeout: 1500
        })
      }
      else {
        incoming.serials.push(serialCode);
        Notify.create({
          position: 'top',
          color: 'theme-green',
          message: `Seriale ${serialCode} aggiunto`,
          timeout: 1500
        })
      }
    })
  }
  newSerialCode.value = ''
  document.getElementById('serial-input').focus();
}

function next() {
  incoming.stage = 'position';
}

function back() {
  incoming.serials = [];
  incoming.product = undefined;
  incoming.stage = 'product'
}

</script>
