<template>
  <q-dialog ref="dialogRef" no-backdrop-dismiss no-shake @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-card-section class="q-mb-md">
        <div
          class="text-h2 highlight text-center"
          style="font-family: 'Red Hat Display'"
        >
          {{ $t('batch_serial_select') }}
        </div>
      </q-card-section>
      <q-form id="serial-form" @submit="onDialogOK(selected_serials)">
        <q-card-section class="row items-center justify-between">
          <q-option-group
            type="toggle"
            :options="available_serials"
            :model-value="selected_serials"
            @update:model-value="ensureMaxQuantity"
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
            form="serial-form"
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
import { useDialogPluginComponent, useQuasar } from 'quasar';
import { ref } from 'vue';

const props = defineProps({
  available_serials: {
    type: [String, Object, null],
    required: true,
  },
  selected_serials: {
    type: Array,
    default: () => [],
  },
  max_quantity: {
    type: Number,
    required: true
  }
});

const $q = useQuasar()
// TODO: Add control to avoid selecting more than the remaining quantity for the job

let available_serials = ref(props.available_serials);
let selected_serials = ref(props.selected_serials);

defineEmits(useDialogPluginComponent.emitsObject);

function ensureMaxQuantity(value) {
  if (value.length > props.max_quantity) {
    $q.notify({
      // TODO: message translation
      message: "Max quantity reached",
      color: 'theme-yellow',
      timeout: 1500,
      position: 'top',
    });
  }
  else {
    selected_serials.value = value
  }
}

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } =
  useDialogPluginComponent();
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
