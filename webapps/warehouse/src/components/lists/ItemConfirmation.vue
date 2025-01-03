<template>
    <!-- ITEM CODE & DESCRIPTION -->
    <div class="row col-auto">
      <div class="col-8">
        <div class="text-h6 q-mb-sm">
          {{ $t('product') }}
        </div>
        <div class="text-h3 q-pr-sm" style="word-wrap: break-word">
          {{ selectedItem.product_code }}
        </div>
        <div class="text-body2 smaller q-mt-xs ellipsis" style="max-width: 70vw;">
          {{ selectedItem.product_description }}
        </div>
        <div
          v-if="selectedItem.references.purchase_doc"
          class="text-h6 weight-bold uppercase q-mt-xs text-low">
          {{ selectedItem.references.purchase_doc }}
        </div>
      </div>

      <div class="col column items-end">
        <div class="text-h6 q-mb-sm">{{ $t('total') }}</div>
        <div class="text-h3 q-pr-sm">
          {{ selectedItem.qt_confirmed }}
        </div>
      </div>
    </div>

    <div
      v-if="lists.itemSerials.length"
      class="row col-auto q-gutter-x-sm"
    >
      <q-badge
        v-for="serial in lists.itemSerials"
        :key="serial"
        color="theme-green"
        class="text-body2 q-pa-sm highlight"
      >
        {{ serial.serial_code }}
      </q-badge>
    </div>

    <q-icon name="mdi-arrow-down-thin" size="lg" class="col-auto q-mt-md"/>


    <div class="row col-auto items-center justify-between q-mt-lg q-mb-md">
      <div class="text-h6">
        {{$t('destination')}}
      </div>
      <div class="text-h6">
        {{$t('quantity')}}
      </div>
    </div>

    <q-scroll-area class="col q-pb-md">
      <template
        v-for="position in selectedPositions"
        :key="position._key"
      >
        <div class="row items-center q-col-gutter-x-sm">
          <div class="col-auto text-h3">
            {{ position.code }}
          </div>

          <div class="col-auto" v-if="selectedPositions.length > 1">
            <q-btn
              :outline="!position.locked"
              round
              size="xs"
              color="primary"
              :icon="position.locked ? 'mdi-lock-outline' : 'mdi-lock-open-variant-outline'"
              @click="position.locked = !position.locked"
            />
          </div>
          <q-space></q-space>
          <div class="col-auto text-h3 text-right">
            {{ position.quantity }}
          </div>
        </div>

        <div class="row" v-if="selectedPositions.length > 1" >
          <q-slider
            v-model="position.quantity"
            class="q-mb-md"
            style="z-index: 1000"
            :min="0"
            :max="selectedItem.qt_confirmed"
            :step="1"
            :disable="position.locked || allOthersLocked[position._key]"
            @update:model-value="adjust(position)"
          />
        </div>
      </template>
    </q-scroll-area>



</template>

<script setup>
import { computed } from 'vue';
import { useListsStore } from 'stores/lists'
import { storeToRefs } from 'pinia';
const lists = useListsStore();
const { selectedItem } = storeToRefs(lists);

const selectedPositions = defineModel();

const allOthersLocked = computed(() => {
  return selectedPositions.value.reduce((acc, pos) => {
    acc[pos._key] = selectedPositions.value.filter(p => p._key !== pos._key).every(p => p.locked);
    return acc;
  }, {});
})

function adjust(position) {
  // The @change event is triggered before the model is updated

  // Total quantity to distribute
  let quantity_to_adjust = selectedItem.value.qt_confirmed;
  for (const pos of selectedPositions.value) {
    quantity_to_adjust -= pos.quantity;
  }

  // Find the index of the position that is being adjusted
  let position_index = selectedPositions.value.findIndex(
    (pos) => pos._key === position._key
  );

  // Find the next position to adjust
  let next_index = position_index + 1;

  // Distribute the quantity to the next position
  while (quantity_to_adjust !== 0) {
    // If we reach the end of the list, start from the beginning
    if (next_index === selectedPositions.value.length) {
      next_index = 0;
    }
    // assign the delta to the next available position
    let next_position = selectedPositions.value[next_index];
    if (quantity_to_adjust > 0) {
      if (!next_position.locked) {
        next_position.quantity += quantity_to_adjust;
        quantity_to_adjust = 0;
      }
      next_index += 1;
    } else {
      // If the quantity to adjust is negative, distribute it to the next position
      let adjustment = 0 - quantity_to_adjust;
      let possible_adjustment =
        next_position.quantity - adjustment >= 0
          ? adjustment
          : next_position.quantity;
      if (!next_position.locked) {
        next_position.quantity -= possible_adjustment;
        quantity_to_adjust += possible_adjustment;
      }
      next_index += 1;
    }
  }
}
</script>

