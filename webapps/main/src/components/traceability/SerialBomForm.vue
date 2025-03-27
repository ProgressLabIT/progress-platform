<template>
  <BaseDialog
    :show="show"
    @close="
      {
        saving = false;
        emit('close');
      }
    "
  >
    <q-card
      square
      class="surface1 q-pa-md"
      style="min-width: 600px; max-width: 800px"
    >
        <!-- FORM TITLE -->
        <q-card-section>
          <div class="row justify-between items-center">
            <div class="text-h2 display highlight text-center">
              {{ t('serial') + ' #' + batchSerials[index]?.code }}
            </div>
            <div
              v-if="!batchSerials[index]?.code ?? false"
              class="text-italic text-body2 q-ml-md text-low"
            >
              (TEMP ID)
            </div>
          </div>
        </q-card-section>

        <NoDataAlert v-if="!bom">
          {{ t('serial_field.noData') }}
        </NoDataAlert>

        <q-card-section v-else class="column q-gutter-y-md">
          <template
            v-for="line in formLines"
            :key="line.component_key"
          >
          <div class="row q-mb-md">
              <div class="col">
                <BaseAutocompleteSerial
                  :value="line.serials"
                  :label="
                    $capitalize([t('serial'), line.component_code, '-', line.component_description].join(' '))
                  "
                  :hint="t('serial_autocomplete_hint', { minChars: 3 })"
                  :loading="loading"
                  :product_key="line.component_key"
                  :can_create="true"
                  :selection_qt="line.qt"
                  :used-serials="usedSerialsKeys"
                  :filter_used="true"
                  key-only
                  :inventory_in_position_key="line.consumption_options?.consumption_position_key"
                  :filtered_values="usedSerialsKeys"
                  @select="(selection) => emit('select', {selection, bomLine: line, parentSerialKey: batchSerials[index]._key})"
                >
                </BaseAutocompleteSerial>
              </div>
            </div>

            <q-separator class="q-my-md" />
          </template>
        </q-card-section>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <template v-if="batchSerials.length > 1">
              <q-btn
                v-if="index > 0"
                icon="mdi-arrow-left-bold"
                color="theme-blue"
                @click="index = index - 1"
              >
              </q-btn>
              <q-btn
                v-if="index < batchSerials.length - 1"
                icon="mdi-arrow-right-bold"
                color="theme-blue"
                @click="index = index + 1"
              >
              </q-btn>
            </template>
            <q-btn
              v-if="batchSerials"
              color="theme-orange"
              :label="t('save')"
              :loading="saving"
              @click="save"
            >
            </q-btn>

            <q-space />

            <q-btn color="theme-grey" :label="t('cancel')" @click="cancel">
            </q-btn>
          </div>
        </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: true,
  },
  traceability_enabled: {
    type: Boolean,
    default: true,
  },
  batch_key: {
    type: String,
    required: true,
  },
  bom: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['close', 'reset', 'save', 'select']);
const store = useStore();
const { t } = useI18n();

const saving = ref(false);
const batchSerials = ref([]);
const loading = ref(false);
const index = ref(0);

const faked_batch_serials = computed(() => store.state.traceability.current_batch_faked_serials);
const serialLinks = computed(() => store.state.traceability.bom_serials);
const usedSerialsKeys = computed(() => serialLinks.value.map(serial => serial.child_serial_key));

const formLines = computed(() => props.bom.filter(c => c.traceability_level !== null).map(line => ({
  ...line,
  serials: getLineSerials(line),
})));


// Get all component serials for the batch/bom line
function getLineSerials(bomLine) {
  const lineLinks = serialLinks.value.filter(link =>
    link.phase_key == bomLine.phase_key
    && link.component_key == bomLine.component_key
    && link.batch_key == props.batch_key
    && link.parent_serial_key == batchSerials.value[index.value]._key
  )
  // Return array of serial keys if qt > 1 (multiple selection),
  // otherwise return single serial key
  return bomLine.qt > 1
    ? lineLinks.map(link => link.child_serial_key)
    : lineLinks[0]?.child_serial_key;
}

// Get all output serials for the current batch
const getBatchSerials = async () => {
  loading.value = true;
  const { data: batch_serials_data } = await api.get('serial-batch', {
    params: {
      batch_key: props.batch_key,
    },
  });

  batchSerials.value = batch_serials_data;
  loading.value = false;
};

getBatchSerials();

// The following is used when traceability is enabled
// for components, but not for output
const fakeBatchSerials = async () => {
  loading.value = true;

  await store.dispatch('fakeBatchSerials', {
    batch_key: props.batch_key,
  });

  batchSerials.value = faked_batch_serials.value;
  loading.value = false;
};

const save = async () => {
  saving.value = true;
  await store.dispatch('saveSerialLinks')
  saving.value = false;
  emit('close');
};

const cancel = () => {
  emit('reset');
  emit('close');
};

watch(() => props.show, (newVal) => {
  index.value = 0;
  if (!newVal) {
    return;
  }
  if (props.traceability_enabled) {
    getBatchSerials();
  } else {
    fakeBatchSerials();
  }
});
</script>
