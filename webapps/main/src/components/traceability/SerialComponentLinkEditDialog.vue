<template>
  <q-dialog ref="dialogRef" no-backdrop-dismiss no-shake @hide="onDialogHide" backdrop-filter="brightness(0.3)">
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
          :value="selectedSerial"
          :label="
            $capitalize(
              [$t('serial'), start_node?.code || start_node._key].join(' '),
            )
          "
          :hint="$t('serial_autocomplete_hint', { minChars: 3 })"
          :product_key="start_node.product_key"
          :can_create="true"
          :selection_qt="1"
          :filter_used="true"
          @select="onSelect"
        >
        </BaseAutocompleteSerial>
      </q-card-section>

      <q-card-section
        v-if="config.enableInventoryManagement"
        class="row q-col-gutter-x-lg">
        <div class="col-6">
          <q-checkbox
            v-model="processInventory.newLink"
            :disable="selectedSerial?.available === false"
            :label="$t('serial_link_process_inventory.new_link')"
          />
        </div>
        <div class="col-6" v-if="node?._key">
          <q-checkbox
            v-model="processInventory.oldLink"
            :label="$t('serial_link_process_inventory.old_link')"
          />
        </div>
      </q-card-section>

      <q-card-section>
        <q-input
          v-model="reason_model"
          filled
          :label="$t('serial_edit_reason')"
        />
      </q-card-section>


      <q-card-section v-if="showAlert">
        <div class="row q-col-gutter-x-md items-center">
          <div class="col-1">
            <q-icon name="mdi-alert-outline" size="md" color="theme-orange"/>
          </div>
          <div class="col column q-gutter-y-sm">
            <div class="text-h4 highlight">
              {{
                selectedSerial.used
                ? $t('serial_used_confirmation')
                : $t('serial_not_available_confirmation')
              }}
            </div>
            <div>
              {{
                selectedSerial?.used
                ? $t('serial_used_confirmation_message')
                : $t('serial_not_available_confirmation_message')
              }}
            </div>
          </div>
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
          v-if="something_has_changed"
          type="submit"
          form="serial-form"
          :color="!selectedSerial?.available || selectedSerial?.used ? 'theme-orange' : 'theme-blue'"
          padding="md xl"
          :label="selectedSerial === null ? $t('delete') : $t('confirm')"
          @click="save"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { useDialogPluginComponent } from 'quasar';
import { ref, reactive, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import BaseAutocompleteSerial from '../BaseAutocompleteSerial.vue';
import { useConfigStore } from '@/stores/config'

const { t: $t } = useI18n({ useScope: 'global' });
const { config } = useConfigStore()

const props = defineProps({
  node: {
    type: Object,
    required: true,
  },
  serial: {
    type: Object,
    required: true,
  },
});

let start_node = ref(props.node);
let selectedSerial = ref(props.serial);
let reason_model = ref(props.serial.reason);
let processInventory = reactive({
  newLink: true,
  oldLink: true,
});

const something_has_changed = computed(() => {
  return selectedSerial.value?._key != props.serial?._key;
});

const showAlert = computed(() => {
  return selectedSerial.value
          && something_has_changed.value
          && (selectedSerial.value?.used || !selectedSerial.value?.available);
});

defineEmits(useDialogPluginComponent.emitsObject);

const { dialogRef, onDialogHide, onDialogCancel, onDialogOK } =
  useDialogPluginComponent();

function save() {
  if (!reason_model.value) {
    window.alert($t('serial_field.missing_reason'));
    return;
  }
  onDialogOK({
    ...selectedSerial.value,
    processInventory: processInventory,
    reason: reason_model.value,
  });
}

function onSelect(serial) {
  console.log('onSelect', serial);
  selectedSerial.value = serial;
  if (!selectedSerial.value?.available) {
    processInventory.newLink = false;
  }
  console.log('selectedSerial', selectedSerial.value);
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
