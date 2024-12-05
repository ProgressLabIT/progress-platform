<template>
  <div ref="qtyarea">
    <q-card
      v-touch-repeat.mouse="handleRepeat"
      outline
      flat
      class="cursor-pointer row justify-center q-py-md"
      :style="selector_style"
    >
      <q-icon class="absolute-right" color="theme-blue" name="mdi-plus" size="80px" style="opacity: .3"/>
      <q-icon class="absolute-left" color="theme-blue" name="mdi-minus" size="80px" style="opacity: .3"/>
      <div class="col-auto ">
        <q-input v-model="quantity" borderless input-class="text-center text-h1"/>
      </div>
    </q-card>
  </div>
</template>

<script setup>
import { useTemplateRef } from 'vue';

const { selector_style } = defineProps({
  selector_style: {
    type: String,
    default: '',
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
    quantity.value++;
  } else if (quantity.value > 0) {
    quantity.value--;
  }
}
</script>

<style lang="sass" scoped>
</style>
