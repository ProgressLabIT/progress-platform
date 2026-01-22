<template>
  <div class="col column">
    <!-- HEADER -->
    <div class="row col-auto">
      <slot name="heading">
        <div class="col text-h3">{{ heading || $t('quantity') }}</div>
      </slot>
      <div class="col-auto" v-if="quantity > props.max">
        <span class="text-h6 text-theme-orange q-mr-sm">
          Max {{ props.max }}
        </span>
        <q-icon
          name="mdi-alert"
          color="theme-orange"
          size="20px"
        />
      </div>
    </div>

    <q-card
      v-touch-repeat:0:600:600:60.mouse="handleRepeat"
      outline
      flat
      class="cursor-pointer q-my-md surface2 col"
      :class="{ 'warning-border': quantity > props.max }"
      id="qtyarea"
      style="min-height: 45px;"
      :style="selectorStyle"
    >

      <q-icon
        color="theme-blue"
        class="absolute-bottom-left"
        name="mdi-minus"
        size="50px"
        style="opacity: .3"
      />
      <div
        class="absolute-center text-center text-h1"
      > {{ quantity }} </div>
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
      <div class="row q-col-gutter-x-sm">
        <div class="col">
          <q-btn
            color="low"
            outline
            label="-100"
            size="md"
            class="full-width"
            v-touch-repeat:0:600:600:60.mouse="() => addQuantity(-100)"
          />
        </div>
        <div class="col">
          <q-btn
            color="low"
            outline
            label="-10"
            size="md"
            class="full-width"
            v-touch-repeat:0:600:600:60.mouse="() => addQuantity(-10)"
          />
        </div>
        <div class="col">
          <q-btn
            color="theme-blue"
            outline
            label="+10"
            size="md"
            class="full-width"
            v-touch-repeat:0:600:600:60.mouse="() => addQuantity(10)"
          />
        </div>
        <div class="col">
          <q-btn
            color="theme-blue"
            outline
            label="+100"
            size="md"
            class="full-width"
            v-touch-repeat:0:600:600:60.mouse="() => addQuantity(100)"
          />
        </div>
      </div>
      <div class="full-width row q-mt-md" v-if="props.max">
        <div class="col">
          <q-btn
            color="theme-blue"
            outline
            size="md"
            class="full-width"
            @click="setQuantity(props.max)"
          >
            <div class="row full-width justify-between">
              <div class="col">MAX</div>
              <div class="col-1"></div>
              <div class="col">{{ props.max }}</div>
            </div>
          </q-btn>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n';

const { t: $t} = useI18n();

const props = defineProps({
  selectorStyle: {
    type: String,
    default: '',
  },
  heading: {
    type: String,
    default: undefined,
  },
  min: {
    type: Number,
    default: 0,
  },
  max: {
    type: Number,
    default: undefined,
  },
  softMax: {
    // Allow the quantity to go above the max with a warning
    type: Boolean,
    default: false,
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

  // Point is above diagonal if relative y position is less than
  // what y would be at that x position on the diagonal line
  return relativeY < slope * relativeX;
}

function handleRepeat(info) {
  if (isTouchUpRight(info.position)) {
    addQuantity(1);
  } else if (quantity.value > 0) {
    addQuantity(-1);
  }
}

function addQuantity(howMuch) {
  setQuantity(quantity.value + howMuch);
}

function setQuantity(value) {
  if (props.softMax) {
    quantity.value = Math.max(props.min, value);
  } else {
    quantity.value = Math.max(props.min, Math.min(props.max ?? 999999999999, value));
  }
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

.warning-border
  border: 1px solid var(--theme-orange)
</style>
