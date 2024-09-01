<template>
  <q-dialog ref="dialogRef" no-backdrop-dismiss no-shake @hide="onDialogHide">
    <q-card class="dialog-card q-pa-lg surface2">
      <q-card-section class="q-mb-md">
        <div
          class="text-h2 highlight text-center"
          style="font-family: 'Red Hat Display'"
        >
          {{ start_node.product_code }}
        </div>
      </q-card-section>
      <q-card-section>
        <BaseAutocompleteSerial
          v-model="serial_model"
          :label="
            $capitalize(
              [$t('serial'), start_node?.code | start_node._key].join(' '),
            )
          "
          :initial_values="initial_values"
          :product_key="start_node.product_key"
          :can_create="true"
          :selection_qt="1"
          :filter_used="true"
        >
        </BaseAutocompleteSerial>
      </q-card-section>
      <q-card-section>
        <q-input v-model="reason_model" />
      </q-card-section>
      <q-form
        id="serial-form"
        @submit="
          onDialogOK({
            ...serial_model,
            reason: reason_model,
          })
        "
      >
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
import { useDialogPluginComponent } from 'quasar';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseAutocompleteSerial from '../BaseAutocompleteSerial.vue';

const { t: $t } = useI18n({ useScope: 'global' });

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
  serial: {
    type: Object,
    required: true,
  },
  initial_values: {
    type: Object,
    required: true,
  },
});

let start_node = ref(props.node);
let serial_model = ref(props.serial);
let reason_model = ref(props.serial.reason);
let initial_values = ref(props.initial_values);

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
