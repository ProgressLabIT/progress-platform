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
      <q-card-section>
        <q-input
          v-model="serial_search_text"
          filled
          :label="$t('scan_serial')"
          @keyup.enter="selectSerial"
        >
        </q-input>
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
        <q-card-section>
          <q-checkbox
            v-model="selectAll"
            :label="$t('select_all')"
          ></q-checkbox>
          <q-checkbox
            v-model="selectNone"
            :label="$t('deselect_all')"
          ></q-checkbox>
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
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const { t: $t } = useI18n({ useScope: 'global' });

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
    required: true,
  },
});

const $q = useQuasar();

let available_serials = ref(props.available_serials);
let selected_serials = ref(props.selected_serials);
let serial_search_text = ref('');
const selectAll = ref(false);
const selectNone = ref(false);

watch(selectAll, () => {
  if (selectAll.value) {
    for (const serial of available_serials.value) {
      if (!selected_serials.value.includes(serial.value)) {
        selected_serials.value.push(serial.value);
      }
    }
    selectNone.value = false;
  }
});

watch(selectNone, () => {
  if (selectNone.value) {
    selected_serials.value.length = 0;
    selectAll.value = false;
  }
});

defineEmits(useDialogPluginComponent.emitsObject);

function ensureMaxQuantity(value) {
  // Prevent selecting more serials than the remaining quantity for the job
  if (value.length > props.max_quantity) {
    $q.notify({
      // TODO: message translation
      message: $t('max_quantity_reached'),
      color: 'theme-orange',
      timeout: 1500,
      position: 'top',
    });
  } else {
    selected_serials.value = value;
  }
}

function selectSerial() {
  let match = available_serials.value
    .map((serial) => serial.label)
    .indexOf(serial_search_text.value);
  if (match !== -1) {
    const serial_key = available_serials.value[match].value;
    if (!selected_serials.value.includes(serial_key)) {
      selected_serials.value.push(serial_key);
      serial_search_text.value = '';
    }
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
