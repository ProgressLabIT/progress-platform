<template>
  <q-dialog
    v-model="show"
    square
    full-width
    transition-show="slide-up"
    transition-hide="slide-down"
    @hide="emit('hide')"
  >
    <q-card
      class="q-pa-lg absolute-bottom column"
      style="width: 100%"
      :style="{ minHeight: props.minHeight, height: props.height}">
      <slot></slot>
    </q-card>
  </q-dialog>
</template>

<script setup>
const emit = defineEmits(['hide'])

const show = defineModel({
  type: Boolean,
  default: false,
});

const props = defineProps({
  minHeight: {
    type: String,
    default: '50px'
  },
  height: {
    type: String,
    default: null
  }
});

</script>

<style scoped>
/* .slide-up-card {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  transform: translateY(100%);
  transition: transform 0.3s ease-in-out;
}

.slide-up-card-enter-active,
.slide-up-card-leave-active {
  transition: transform 0.3s ease-in-out;
}

.slide-up-card-enter, .slide-up-card-leave-to {
  transform: translateY(100%);
} */
.q-dialog__inner--minimized > div {
  max-height: 99vh !important;
}
</style>
