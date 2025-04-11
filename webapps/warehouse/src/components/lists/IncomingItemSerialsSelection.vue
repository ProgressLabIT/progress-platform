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

  <div class="row col-auto items-center q-mt-md q-mb-sm q-gutter-x-sm">
    <div class="text-h6">
      Selezionati
    </div>
    <q-chip size="xs" color="theme-grey">
      <div class="smaller highlight">{{ lists.tempSerials.length }} / {{ lists.selectedItem.qt_planned - movementsCompleted.length }}</div>
    </q-chip>

    <!-- SELECT/UNSELECT ALL - ONLY WITH SERIALS PROVIDED -->
    <template v-if="lists.selectedItem.serialsProvided">
      <q-space></q-space>
      <q-btn color="theme-grey" size="xs" padding="xs md" icon="mdi-checkbox-multiple-blank-outline" @click="() => toggleAll(false)" />
      <q-btn color="theme-blue" size="xs" padding="xs md" icon="mdi-checkbox-multiple-marked" @click="() => toggleAll(true)" />
    </template>
  </div>

  <!-- SERIALS LIST -->
  <q-scroll-area class="col q-mt-md">
    <div class="col-auto row q-gutter-sm">
      <q-card
        v-for="serial in shownSerials"
        :key="serial"
        flat
        :bordered="serialsProvided.includes(serial) && !lists.tempSerials.includes(serial)"
        class="q-pa-sm"
        :class="{'bg-theme-green highlight': lists.tempSerials.includes(serial)}"
        @click="toggleItem(serial)"
      >
        {{ serial }}
      </q-card>
    </div>
  </q-scroll-area>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useListsStore } from 'app/src/stores/lists';
import { Notify } from 'quasar';
import {api} from '@/boot/axios'

const lists = useListsStore()


const newSerialCode = ref('');

// Assumption: if one serial is provided, all must be provided
// Do not use computed, as movements will be updated with new serials as they get added
const serialsProvided = lists.selectedItem.movements
  .filter(m => m.serial_code && m.status == 'planned' && m._key)
  .map(m => m.serial_code)
  .toSorted()
const movementsCompleted = lists.selectedItem.movements.filter(m => m.status === 'completed')

const shownSerials = computed(() => {
  return serialsProvided?.length ? serialsProvided : lists.tempSerials
})


function resetInput() {
  newSerialCode.value = ''
  document.getElementById('serial-input').focus()
}

function toggleAll(select) {
  if (select) {
    lists.tempSerials = [...serialsProvided]
    lists.selectedItem.qt_confirmed = serialsProvided.length + movementsCompleted.length
    Notify.create({
      position: 'top',
      color: 'theme-green',
      message: `${lists.tempSerials.length} seriali selezionati`,
      timeout: 1500
    })
  } else {
    lists.tempSerials = []
    lists.selectedItem.qt_confirmed = movementsCompleted.length
    Notify.create({
      position: 'top',
      color: 'theme-grey',
      message: `Seriali rimossi`,
      timeout: 1500
    })
  }
}

async function isInInventory(serialCode) {
  const { data: inventory } = await api.get(`/inventory`, { params: { serial_code: serialCode, product_key: lists.selectedItem.product_key } })
  return inventory.some(i => i.serial_code === serialCode)
}

async function toggleItem(serialCode) {
  // If no serial code is provided, notify the user
  if (!serialCode?.length) {
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: `Seriale non valido`,
      timeout: 1500
    })
    return
  }


  // If the serial code is already selected, unselect it
  if (lists.tempSerials.includes(serialCode)) {
    // Remove selected serial
    lists.tempSerials.splice(lists.tempSerials.indexOf(serialCode), 1)
    lists.selectedItem.qt_confirmed -= 1
    Notify.create({
      position: 'top',
      color: 'theme-grey',
      message: `Seriale ${serialCode} rimosso`,
      timeout: 1500
    })
  }

  // Check if the serial is already in inventory
  else if (await isInInventory(serialCode)) {
    Notify.create({
      position: 'top',
      color: 'theme-grey',
      message: `Seriale ${serialCode} già presente nel magazzino`,
      timeout: 1500
    })
  }

  // Handle the case where serials are provided
  else if (serialsProvided.length && !serialsProvided.includes(serialCode)) {
    // Allow only serials among the provided ones
    Notify.create({
      position: 'top',
      color: 'theme-orange',
      message: `Seriale ${serialCode} non presente fra quelli previsti`,
      timeout: 1500
    })
  }
  else {
    lists.tempSerials.push(serialCode)
    lists.selectedItem.qt_confirmed += 1
    Notify.create({
      position: 'top',
      color: 'theme-green',
      message: `Seriale ${serialCode} aggiunto`,
      timeout: 1500
    })
  }
  resetInput()
}


</script>
