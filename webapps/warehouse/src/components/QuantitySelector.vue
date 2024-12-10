<template>
  <div ref="qtyarea" class="col column">
    <q-card
      v-touch-repeat.mouse="handleRepeat"
      outline
      flat
      class="cursor-pointer q-my-md surface2 col"
      :style="selector_style"
    >
    <div class="row justify-between full-height">

      <q-icon color="theme-blue" class="self-end" name="mdi-minus" size="80px" style="opacity: .3"/>
      <div class="col self-center">
        <q-input type="number" v-model.number="quantity"  borderless input-class="text-center text-h1"/>
      </div>
      <q-icon color="theme-blue" class="self-start" name="mdi-plus" size="80px" style="opacity: .3"/>
    </div>
    </q-card>

    <!-- ±10/100 -->
     <template v-if="showButtons">
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
      </template>
  </div>
</template>

<script setup>
import { useTemplateRef } from 'vue';

const props = defineProps({
  selector_style: {
    type: String,
    default: '',
  },
  min: {
    type: Number,
    default: 0,
  },
  max: {
    type: Number,
    default: 999999999999,
  },
  showButtons: {
    type: Boolean,
    default: false,
  },
})

const quantity = defineModel({ type: Number })

const quantityArea = useTemplateRef('qtyarea')


function isTouchUpRight(touchPosition) {
  // Quantity Area top-left/bottom-right diagonal: y = ax + b
  // with y = top, x = left, b = rect.top (origin y)
  const rect = quantityArea.value.getBoundingClientRect();
  const a = rect.height / rect.width
  const b = rect.top - rect.left * a
  // y < ax + b
  return touchPosition.top < a * touchPosition.left + b
}

function handleRepeat(info) {
  if (isTouchUpRight(info.position)) {
    updateQuantity(1);
  } else if (quantity.value > 0) {
    updateQuantity(-1);
  }
}

function updateQuantity(howMuch) {
  quantity.value = Math.max(props.min, Math.min(props.max, quantity.value + howMuch));
}
</script>

<style lang="sass" scoped>
</style>
