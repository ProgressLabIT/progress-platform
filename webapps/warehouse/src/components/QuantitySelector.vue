<template>
  <div class="col column">
    <q-card
      v-touch-repeat.mouse="handleRepeat"
      outline
      flat
      class="cursor-pointer q-my-md surface2 col"
      id="qtyarea"
      :style="selectorStyle"
    >

      <q-icon
        color="theme-blue"
        class="absolute-bottom-left"
        name="mdi-minus"
        size="50px"
        style="opacity: .3"
      />
      <q-input
        class="absolute-center"
        type="number"
        v-model.number="quantity"
        borderless
        input-class="text-center text-h1"
      />
      <q-icon
        color="theme-blue"
        class="absolute-top-right"
        name="mdi-plus"
        size="50px"
        style="opacity: .3"
      />
    </q-card>

    <!-- ±10/100 -->
     <template v-if="showButtons">
    <div class="full-width row q-mt-md">
        <div class="col">
          <q-btn
            color="theme-blue"
            outline
            label="-10"
            size="md"
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
            size="md"
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
            size="md"
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
            size="md"
            class="full-width"
            @click="updateQuantity(100)"
          />
        </div>
      </div>
      </template>
  </div>
</template>

<script setup>

const props = defineProps({
  selectorStyle: {
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
  }
})

const quantity = defineModel({ type: Number })



function isTouchUpRight(touchPosition) {
  // Get the bounding rectangle of the quantity area
  const quantityArea = document.getElementById('qtyarea')
  const rect = quantityArea.getBoundingClientRect();

  // Convert touch position to be relative to the rectangle's top-left corner
  const relativeX = touchPosition.left - rect.left;
  const relativeY = touchPosition.top - rect.top;

  // Calculate slope of diagonal line from top-left to bottom-right
  const slope = rect.height / rect.width;
  console.log(slope);

  // Point is above diagonal if relative y position is less than
  // what y would be at that x position on the diagonal line
  return relativeY < slope * relativeX;
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
.diagonal-line
  position: absolute
  width: 141.4% // √2 * 100% to account for rotation
  height: 1px
  background-color: rgba(255, 0, 0, 0.3)
  top: 50%
  left: 50%
  transform: translate(-50%, -50%) rotate(45deg)
  transform-origin: center
  pointer-events: none
  z-index: 1
</style>
