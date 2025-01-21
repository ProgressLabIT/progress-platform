<template>
  <!-- ITEM CODE & DESCRIPTION -->
  <div class="col-auto">
    <div class="text-h6 q-mb-sm">
      {{ $t('product') }}
    </div>
    <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
      {{ lists.selectedItem.product_code }}
    </div>
    <div class="text-body2 smaller q-mt-xs">
      {{ lists.selectedItem.product_description }}
    </div>
    <div
      v-if="lists.selectedItem.references.purchase_doc"
      class="text-h6 weight-bold uppercase q-mt-xs text-low">
      {{ lists.selectedItem.references.purchase_doc }}
    </div>
  </div>


    <div class="col-auto text-h3 q-mt-md q-mb-sm">
      Inserisci seriali
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

  <!-- SERIALS -->
  <div class="row col-auto items-center q-mt-md q-mb-sm q-gutter-x-sm">
    <div class="text-h6">
      Selezionati
    </div>
    <q-chip size="xs" color="theme-grey">
      <div class="smaller highlight">{{ lists.itemSerials.length }} / {{ lists.selectedItem.qt_planned }}</div>
    </q-chip>
    <q-space></q-space>
    <q-btn color="theme-grey" size="xs" padding="xs md" icon="mdi-checkbox-multiple-blank-outline" @click="() => toggleAll(false)" />
    <q-btn color="theme-blue" size="xs" padding="xs md" icon="mdi-checkbox-multiple-marked" @click="() => toggleAll(true)" />

    </div>
  <q-scroll-area class="col q-mt-md">
    <div class="col-auto row q-gutter-sm">
      <q-card
        v-for="serial in lists.itemSerials.concat(availableSerials)"
        :key="serial._key"
        flat
        :bordered="serial.qt_confirmed === 0"
        class="q-pa-sm"
        :class="{ 'bg-theme-green highlight': serial.qt_confirmed === 1 }"
        @click="toggleItem(serial.serial_code)"
      >
        {{ serial.serial_code }}
      </q-card>
    </div>
  </q-scroll-area>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useListsStore } from 'app/src/stores/lists';
import { Notify } from 'quasar';

const lists = useListsStore()


const newSerialCode = ref('');

function resetInput() {
  newSerialCode.value = ''
  document.getElementById('serial-input').focus()
}

const availableSerials = computed(() => {
  return lists.selectedItem.movements
    .filter(m => m.status == 'planned' && !lists.itemSerials.some(s => s.serial_code == m.serial_code))
    .sort((a, b) => a.serial_code.localeCompare(b.serial_code))
})

function toggleAll(select) {
  if (select) {
    lists.selectedItem.movements.forEach(m => m.qt_confirmed = 1)
    lists.selectedItem.qt_confirmed = lists.selectedItem.movements.length
  } else {
    lists.selectedItem.movements.forEach(m => m.qt_confirmed = 0)
    lists.selectedItem.qt_confirmed = 0
  }
}

function toggleItem(serialCode) {
  const match = lists.selectedItem.movements.find(m => m.serial_code == serialCode)
  if (match) {
    if (match.qt_confirmed === 1) {
      match.qt_confirmed = 0
      lists.selectedItem.qt_confirmed -= 1
      resetInput()
      Notify.create({
        position: 'top',
        color: 'theme-grey',
        message: `Seriale ${serialCode} rimosso`,
        timeout: 1500
      })
    }
    else {
      match.qt_confirmed = 1
      lists.selectedItem.qt_confirmed += 1
      resetInput()
      Notify.create({
        position: 'top',
        color: 'theme-green',
        message: `Seriale ${serialCode} aggiunto`,
        timeout: 1500
      })
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
