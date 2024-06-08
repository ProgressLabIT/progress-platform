<template>
  <q-dialog ref="dialogRef" no-backdrop-dismiss no-shake @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-card-section class="q-mb-md">
        <div
          class="text-h2 highlight text-center"
          style="font-family: 'Red Hat Display'"
        >
          {{ $t('batch_declare_serial') }}
        </div>
      </q-card-section>
      <q-form id="serial-declare" @submit="onDialogOK(batch_serials)">
        <q-card-section class="row items-center justify-between">
          <div
            v-for="serial in batch_serials"
            :key="serial._key"
            class="q-py-xs"
          >
            <q-input
              v-model="serial.serial"
              dense
              filled
              stack-label
              autogrow
              lazy-rules
              input-debounce="100"
              hide-bottom-space
            >
            </q-input>
          </div>
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
            form="serial-declare"
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
  batch_serials: {
    type: [String, Object, []],
    required: true,
  },
});

let batch_serials = ref(props.batch_serials);

defineEmits(useDialogPluginComponent.emitsObject);

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
