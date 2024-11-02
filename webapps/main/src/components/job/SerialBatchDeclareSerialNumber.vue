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
            :key="serial.serial_key"
            class="q-py-xs full-width"
          >
            <q-input
              filled
              stack-label
              autogrow
              lazy-rules
              input-debounce="100"
              hide-bottom-space
              :model-value="serial.serial_code"
              @update:model-value="
                (v) => (serial.serial_code = v.toUpperCase())
              "
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
            form="serial-declare"
            color="primary"
            padding="md xl"
            :label="$t('confirm')"
            @click="verifySerialCode"
          />
        </q-card-actions>
      </q-form>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent, useQuasar } from 'quasar';
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';

const props = defineProps({
  batch_serials: {
    type: [String, Object, []],
    required: true,
  },

  product_key: {
    type: String,
    required: true,
  },
});
const $q = useQuasar();
const { t: $t } = useI18n({ useScope: 'global' });

let batch_serials = ref(props.batch_serials);
let product_key = ref(props.product_key);

defineEmits(useDialogPluginComponent.emitsObject);

async function verifySerialCode() {
  let serials_free = true;
  for (const serial of batch_serials.value) {
    const { data } = await api.get('/serial-code/verify-free', {
      params: {
        serial_code: serial.serial_code,
        product_key: product_key.value,
        serial_key: serial.serial_key,
      },
    });
    serials_free = serials_free && data;
    if (!data) {
      $q.notify({
        // TODO: message translation
        message: $t('serial_field.create.code_already_used', {
          name: serial.serial_code,
        }),
        color: 'theme-orange',
        timeout: 1500,
        position: 'top',
      });
    }
  }
  if (serials_free) {
    onDialogOK(batch_serials.value);
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
