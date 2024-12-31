<template>
  <!-- ITEM CODE & DESCRIPTION -->
  <div class="col-auto">
    <div class="text-h6 q-mb-sm">{{ $t('product') }}</div>
    <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
      {{ item.product_code }}
    </div>
    <div class="text-body2 smaller q-mt-xs">
      {{ item.product_description }}
    </div>
    <div
      v-if="item.references.purchase_doc"
      class="text-h6 weight-bold uppercase q-mt-xs text-low">
      {{ item.references.purchase_doc }}
    </div>
  </div>

  <div class="row items-center q-mt-lg q-mb-sm">

    <div class="col-auto text-h3 q-mr-sm">
      Inserisci seriali
    </div>

    <q-chip v-if="selectedSerials.size" size="xs" color="theme-grey">
      <div class="smaller highlight">{{ selectedSerials.size }}</div>
    </q-chip>

  </div>

  <div class="col-auto row">
  <q-input
    filled
    dense
    for="serial-input"
    autofocus
    clearable
    class="col"
    input-class="text-uppercase"
    :model-value="newSerialCode"
    @update:model-value="(value) => newSerialCode = value?.toUpperCase()"
    @keyup.enter="() => toggleItem(newSerialCode)"
  >
  </q-input>
  <q-btn
    color="theme-blue"
    unelevated
    padding="xs md"
    icon="mdi-plus"
    class="col-auto q-ml-md"
    :disabled="newSerialCode?.length === 0"
    @click="() => toggleItem(newSerialCode)"
  />
  </div>

  <q-scroll-area class="col q-mt-lg">
    <div class="col-auto row q-gutter-md">
      <q-card
        v-for="serialCode in selectedSerials"
        :key="serialCode"
        flat
        class="bg-theme-blue q-pa-sm highlight"
        @click="toggleItem(serialCode)"
      >
        {{ serialCode }}
      </q-card>
    </div>
  </q-scroll-area>
</template>

<script setup>
import { ref } from 'vue';
// import { useListsStore } from 'app/src/stores/lists';
import { Notify } from 'quasar';
import { useI18n } from 'vue-i18n';

const { t: $t } = useI18n()

const props = defineProps({
  item: {
    type: Object,
    required: true
  }
});

// const lists = useListsStore();
const newSerialCode = ref('');
const selectedSerials = ref(new Set);
// const movementList = lists.movements

function resetInput() {
  newSerialCode.value = ''
  document.getElementById('serial-input').focus()
}

function toggleItem(serialCode) {
  const match = props.item.movements.find(m => m.serial_code == serialCode)
  if (match) {
    if (selectedSerials.value.has(serialCode)) {
      selectedSerials.value.delete(serialCode)
      resetInput()
    }
    else {
      selectedSerials.value.add(serialCode)
      resetInput()
    }
  }
  else {
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: `Seriale ${serialCode} non presente fra quelli previsti`,
      timeout: 2000
    })
  }
}


</script>
