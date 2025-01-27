<template>
  <q-scroll-area class="col column q-col-gutter-y-md full-width">
    <div
      v-for="position in positions"
      :key="position._key"
      class="col"
      >
      <div class="row items-center q-col-gutter-x-md">
      <div class="col-auto text-h3">
        {{ position.code }}
      </div>

      <div class="col-auto" v-if="positions.length > 1">
        <q-btn
          :outline="!position.locked"
          round
          size="xs"
          color="primary"
          :icon="
                position.locked
                ? 'mdi-lock-outline'
                : 'mdi-lock-open-variant-outline'
                "
          @click="updatePositionLock(position)"
          />
        </div>

        <q-space></q-space>
        <div class="col-auto text-h3 text-right">
          {{ position.quantity }}
        </div>
      </div>


      <div class="row items-center q-col-gutter-x-md q-mb-md" v-if="positions.length > 1" >
        <div class="col">
          <q-slider
            v-model="position.quantity"
            style="z-index: 1000"
            :min="0"
            :max="refQuantity"
            :inner-max="Math.max(position.quantity, freeQuantity)"
            :step="1"
            :disable="position.locked || allOthersLocked[position._key]"
            @change="adjust(position)"
          />
        </div>
        <div class="col-auto">
          <q-btn
            round
            flat
            size="sm"
            color="theme-blue"
            icon="mdi-minus"
            @click="() => { position.quantity -= 1; adjust(position) }"
          />
        </div>
        <div class="col-auto">
          <q-btn
            round
            flat
            size="sm"
            color="theme-blue"
            padding="0px"
            icon="mdi-plus"
            @click="() => { position.quantity += 1; adjust(position) }"
          />
        </div>
      </div>
    </div>
  </q-scroll-area>
</template>

<script setup>
import { computed, ref } from 'vue';

const positions = defineModel('positions');
const refQuantity = defineModel('refQuantity');
const freeQuantity = ref(refQuantity.value);

const allOthersLocked = computed(() => {
  return positions.value.reduce((acc, pos) => {
    acc[pos._key] = positions.value.filter(p => p._key !== pos._key).every(p => p.locked);
    return acc;
  }, {});
});


function updatePositionLock(position) {
  position.locked = !position.locked;
  freeQuantity.value = positions.value.filter(p => !p.locked).reduce((acc, p) => acc + p.quantity, 0);
}

function adjust(position) {
  let quantity_to_adjust = refQuantity.value;
  for (const pos of positions.value) {
    quantity_to_adjust -= pos.quantity;
  }

  let position_index = positions.value.findIndex(
    (pos) => pos._key === position._key
  );

  let next_index = position_index + 1;

  while (quantity_to_adjust !== 0) {
    if (next_index === positions.value.length) {
      next_index = 0;
    }
    let next_position = positions.value[next_index];
    if (quantity_to_adjust > 0) {
      if (!next_position.locked) {
        next_position.quantity += quantity_to_adjust;
        quantity_to_adjust = 0;
      }
      next_index += 1;
    } else {
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
