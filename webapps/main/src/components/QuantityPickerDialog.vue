<template>
  <q-dialog ref="dialogRef" no-backdrop-dismiss no-shake @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-card-section class="q-mb-md">
        <div
          class="text-h2 highlight text-center"
          style="font-family: 'Red Hat Display'"
        >
          {{ $t('batch_completed_quantity_question') }}
        </div>
      </q-card-section>
      <q-form id="quantity-form" @submit="onDialogOK(quantity)">
        <q-card-section class="row items-center justify-between">
          <q-btn
            round
            flat
            icon="mdi-minus"
            size="2.5em"
            :disable="quantity === 1"
            @click="decrement"
          />

          <q-input
            v-model.number="quantity"
            type="number"
            class="col q-mx-xl text-h1 number-input"
            filled
            stack-label
            hide-bottom-space
            min="1"
            :max="max"
          />

          <q-btn
            flat
            round
            icon="mdi-plus"
            size="2.5em"
            :disable="quantity === max"
            @click="increment"
          />
        </q-card-section>

        <q-card-section class="q-mt-sm">
          <q-slider
            v-model.number="quantity"
            min="1"
            :max="max"
            color="primary"
            :marker-labels="{
              1: 1,
              [max]: max,
            }"
            marker-labels-class="text-h3 q-mt-xs"
            track-size="6px"
            thumb-size="36px"
            class="q-px-sm"
          />
        </q-card-section>

        <q-card-actions align="between" class="q-mt-md">
          <q-btn
            color="theme-grey"
            padding="md xl"
            :label="$t('cancel')"
            @click="onDialogCancel"
          />

          <q-btn
            type="submit"
            form="quantity-form"
            color="primary"
            padding="md xl"
            :label="$t('confirm')"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';

const props = defineProps({
  initialValue: {
    type: Number,
    default: 1,
  },
  min: {
    type: Number,
    default: 0,
  },
  max: {
    type: Number,
    required: true,
  },
});

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } =
  useDialogPluginComponent();

// It's between min and max, except when the user uses the input field
// It's validated on submit, so we don't need to worry about it
const quantity = ref(props.initialValue);

// Mimics the behavior of the native number input
function decrement() {
  if (quantity.value > props.max) {
    quantity.value = props.max;
  } else if (quantity.value == 1) {
    quantity.value = 1;
  } else {
    quantity.value--;
  }
}

// Mimics the behavior of the native number input
function increment() {
  if (quantity.value < 1) {
    quantity.value = 1;
  } else if (quantity.value > props.max) {
    quantity.value = props.max;
  } else {
    quantity.value++;
  }
}
</script>

<style lang="scss" scoped>
.dialog-card {
  min-width: 650px;
  max-width: 800px;
}

.number-input :deep(.q-field__control) {
  height: 1.25em;
  font-size: 6rem;

  .q-field__native {
    text-align: center;
  }
}
</style>
