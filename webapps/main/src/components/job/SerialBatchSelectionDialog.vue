<template>
  <q-dialog ref="dialogRef" no-backdrop-dismiss no-shake @hide="onDialogHide">
    <q-card
      class="dialog-card q-pa-lg surface1 column q-col-gutter-sm full-height"
    >
      <q-card-section class="col-auto">
        <div
          class="text-h2 highlight text-center"
          style="font-family: 'Red Hat Display'"
        >
          {{ $t('batch_serial_select') }}
        </div>
      </q-card-section>
      <q-card-section class="col-auto row justify-between">
        <div class="col q-pr-lg">
          <q-input
            v-model="serial_search_text"
            filled
            :label="$t('scan_serial')"
            @keyup.enter="selectSerial"
          />
        </div>
        <q-btn
          :label="all_selected ? $t('deselect_all') : $t('select_all')"
          size="md"
          :icon="
            all_selected
              ? 'mdi-checkbox-blank-off-outline'
              : 'mdi-checkbox-marked-outline'
          "
          color="theme-grey"
          @click="toggleAll"
        />
      </q-card-section>
      <div>
        <q-separator />
      </div>
      <q-card-section class="col scroll">
        <q-option-group
          type="checkbox"
          inline
          :options="available_serials"
          :model-value="selected_serials"
          @update:model-value="ensureMaxQuantity"
        >
          <template #label="opt">
            <div
              class="text-body1 q-py-md"
              :class="{
                'text-white text-weight-bold': selected_serials.includes(
                  opt.value,
                ),
              }"
            >
              {{ opt.label }}
            </div>
          </template>
        </q-option-group>
      </q-card-section>
      <div>
        <q-separator />
      </div>
      <q-card-actions align="between" class="q-mt-md col-auto">
        <q-btn
          padding="md xl"
          color="theme-grey"
          :label="$t('cancel')"
          @click="onDialogCancel"
        />
        <div class="text-h5 uppercase">
          {{
            $t('countInfo.selectedTotal', {
              count: selected_serials.length,
              total: available_serials.length,
            })
          }}
        </div>
        <q-btn
          padding="md xl"
          form="serial-form"
          color="primary"
          :label="$t('confirm')"
          @click="onDialogOK(selected_serials)"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent, useQuasar } from 'quasar';
import { ref, computed } from 'vue';
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
let all_selected = computed(
  () => available_serials.value.length === selected_serials.value.length,
);

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

function toggleAll() {
  if (all_selected.value) {
    selected_serials.value = [];
  } else {
    selected_serials.value = available_serials.value.map((s) => s.value);
  }
}

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } =
  useDialogPluginComponent();
</script>

<style lang="scss" scoped>
.dialog-card {
  min-width: 650px;
  max-width: 800px;
  max-height: 98%;
}

.number-input :deep(.q-field__control) {
  height: 1.25em;
  font-size: 6rem;

  .q-field__native {
    text-align: center;
  }
}
</style>

<style lang="scss">
.q-option-group.q-option-group--inline > div {
  width: 230px;
  border-radius: 4px;
  padding-right: 24px;
  // border: 1px solid;
  // background-color: blue;
}

.q-option-group.q-option-group--inline div {
  overflow-wrap: anywhere;
  letter-spacing: 0.7px !important;
}
</style>
