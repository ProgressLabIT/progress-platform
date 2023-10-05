<template>
  <q-dialog ref="dialogRef" @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-card-section class="row items-center justify-between">
        <q-btn
          round
          color="primary"
          icon="mdi-minus"
          size="2.5em"
          :disable="quantity === min"
          @click="quantity--"
        />

        <q-input
          v-model.number="quantity"
          type="number"
          class="col q-mx-xl number-input"
          filled
          stack-label
          hide-bottom-space
          :min="min"
          :max="max"
        />

        <q-btn
          round
          color="primary"
          icon="mdi-plus"
          size="2.5em"
          :disable="quantity === max"
          @click="quantity++"
        />
      </q-card-section>

      <q-card-section class="q-mt-sm">
        <q-slider
          v-model.number="quantity"
          :min="min"
          :max="max"
          :step="1"
          snap
          color="primary"
          markers
          :marker-labels="{
            [min]: min,
            [max]: max
          }"
          marker-labels-class="text-h3 q-mt-xs"
          track-size="12px"
          thumb-size="36px"
          class="q-px-sm"
        />
      </q-card-section>

      <q-card-actions align="between" class="q-mt-md">
        <q-btn flat color="theme-grey" size="xl" label="Cancel" @click="onDialogCancel" />
        <q-btn color="primary" size="xl" label="Confirm" @click="onDialogOK(quantity)" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar'
import { ref } from 'vue'

const props = defineProps({
  initialValue: {
    type: Number,
    default: 1
  },
  min: {
    type: Number,
    default: 0
  },
  max: {
    type: Number,
    required: true
  }
})

defineEmits(useDialogPluginComponent.emitsObject)

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } = useDialogPluginComponent()

const quantity = ref(props.initialValue)
</script>

<style lang="scss" scoped>
.dialog-card {
  min-width: 650px;
  max-width: 800px;
}

.number-input :deep(.q-field__control) {
  height: 1.25em;
  font-size: 10em;

  .q-field__native {
    text-align: center;
  }
}
</style>
