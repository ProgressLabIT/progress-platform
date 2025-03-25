<template>
  <BaseDialog
    :show="show"
    @close="
      {
        saving = false;
        $emit('close');
      }
    "
  >
    <q-card
      square
      class="surface1 q-pa-md"
      style="min-width: 600px; max-width: 800px"
    >
        <!-- FORM TITLE -->
        <q-card-section class="column">
          <div class="text-h2 display highlight">
            {{ component_code }}
          </div>
          <div class="text-body1">
            {{ bom_line.component_description }}
          </div>
        </q-card-section>

        <NoDataAlert v-if="!batch_serials">
          {{ $t('serial_field.noData') }}
        </NoDataAlert>

        <q-card-section v-else class="column q-gutter-y-md">
          <template v-for="serial in batch_serials" :key="serial._id">
            <div class="row q-mb-md">
              <div class="col">
                <BaseAutocompleteSerial
                  v-model="serialModel[serial._id]"
                  :initial_values="initialModel[serial._id]"
                  :label="
                    $capitalize(
                      [$t('serial'), serial?.code || serial._key].join(' '),
                    )
                  "
                  :hint="$t('serial_autocomplete_hint', { minChars: 3 })"
                  :product_key="component_key"
                  :loading="loading"
                  :can_create="true"
                  :selection_qt="component_per_product"
                  :filter_used="true"
                  :filtered_values="booked_serials"
                  :disable="disableSerialField(serial)"
                  :inventory_in_position_key="bom_line?.consumption_options?.consumption_position_key"
                  @select="(selection) => onSerialSelection(selection, serial._id)"
                >
                </BaseAutocompleteSerial>
              </div>
              <div
                v-if="
                  !replace_serials[serial._id] &&
                  phase_key === bom_line?.phase_key
                "
                class="col-auto q-ml-md"
              >
                <q-btn
                  flat
                  round
                  icon="mdi-pencil"
                  :disable="phase_key !== bom_line?.phase_key"
                  @click="replace_serials[serial._id] = true"
                />
              </div>
            </div>
            <q-input
              class="q-mt-sm"
              v-if="replace_serials[serial._id]"
              v-model="replace_serials_reason[serial._id]"
              label="Ragione della modifica"
              filled
            />
            <q-separator class="q-my-md" />

          </template>
        </q-card-section>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="batch_serials"
              color="theme-orange"
              :label="$t('save')"
              :loading="saving"
              @click="
                () => {
                  save();
                }
              "
            >
            </q-btn>

            <q-space />

            <q-btn color="theme-grey" :label="$t('cancel')" @click="cancel">
            </q-btn>
          </div>
        </q-card-section>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import { useI18n } from 'vue-i18n';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import { timestamp } from '@/lib/TimeHandling.js';

const { t: $t } = useI18n();

// Props definition
const props = defineProps({
  show: {
    type: Boolean,
    default: true,
  },
  traceability_enabled: {
    type: Boolean,
    default: true,
  },
  bom_line: {
    type: Object,
    default: null,
  },
  batch_key: {
    type: String,
    default: null,
  },
  phase_key: {
    type: String,
    required: true,
  },
  wo_key: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['close']);

// Store setup
const store = useStore();

// Reactive state
const saving = ref(false);
const enableSave = ref(false);
const serialModel = ref([]);
const initialModel = ref([]);
const initialValues = ref([]);
const batch_serials = ref([]);
const replace_serials = ref([]);
const replace_serials_reason = ref([]);
const loading = ref(false);
const booked_serials = ref([]);

// Computed properties
const faked_batch_serials = computed(() => store.state.traceability.current_batch_faked_serials);
const session_data = computed(() => store.state.session);
const component_code = computed(() => props.bom_line.component_code);
const component_key = computed(() => props.bom_line.component_key);
const component_per_product = computed(() => {
  if (props.traceability_enabled) {
    return props.bom_line.qt;
  } else {
    return props.bom_line?.batch_qt;
  }
});

// Methods
const getBatchSerials = async () => {
  if (!props.batch_key) {return};
  loading.value = true;
  const { data: serials } = await api.get('serial-batch', {
    params: { batch_key: props.batch_key },
  });
  batch_serials.value = serials;
  fillInitialData();
  loading.value = false;
};

const fakeBatchSerials = async () => {
  loading.value = true;
  await store.dispatch('fakeBatchSerials', {
    batch_key: props.batch_key,
  });
  batch_serials.value = faked_batch_serials.value;
  fillInitialData();
  loading.value = false;
};

const initFormData = () => {
  saving.value = false;
  enableSave.value = false;
};

const fillInitialData = () => {
  serialModel.value = [];
  initialModel.value = [];
  initialValues.value = [];
  replace_serials.value = [];
  booked_serials.value = [];
  for (const serial of batch_serials.value) {
    if (!serialModel.value[serial._id]) {
      serialModel.value[serial._id] = [];
      initialModel.value[serial._id] = [];
      replace_serials.value[serial._id] = false;
      replace_serials_reason.value[serial._id] = null;
    }
    for (const child of serial.children) {
      if (child.product_key === component_key.value && child.batch_key === props.batch_key) {
        let serial_link = {
          _key: child._key,
          label: child.code,
          product_key: child.product_key,
          wo_key: child.wo_key,
          value: child._key,
        };
        if (component_per_product.value > 1) {
          serialModel.value[serial._id].push(serial_link);
          initialModel.value[serial._id].push(serial_link);
        } else {
          serialModel.value[serial._id] = serial_link;
          initialModel.value[serial._id] = serial_link;
        }
        booked_serials.value.push(child.code);
        initialValues.value.push({
          parent_serial_key: serial._key,
          child_serial_key: child._key,
          wo_key: child.wo_key,
          component_key: child.product_key,
          batch_key: props.batch_key,
          replaced: true,
          reason: null,
        });
      }
    }
  }
};

const disableSerialField = (serial) => {
  const full_quantity_recorded =
    component_per_product.value === 1
      ? serialModel.value[serial._id] && serialModel.value[serial._id]?._key
      : serialModel.value[serial._id]?.length >= component_per_product.value;
  const not_replaced = !replace_serials.value[serial._id];
  const different_phase = props.phase_key !== props.bom_line?.phase_key;
  return (full_quantity_recorded && not_replaced) || different_phase;
};

const onSerialSelection = (selectedSerials, selected_key) => {
  let temp_booked_serials = new Array();

  if (Array.isArray(selectedSerials)) {
    for (const serial of selectedSerials) {
      temp_booked_serials.push(serial);
    }
  } else if (selectedSerials) {
    temp_booked_serials.push(selectedSerials);
  }

  for (const serial of batch_serials.value) {
    if (serialModel.value[serial._id] && selected_key !== serial._id) {
      if (Array.isArray(serialModel.value[serial._id])) {
        for (const serial_to of serialModel.value[serial._id]) {
          temp_booked_serials.push(serial_to);
        }
      } else {
        temp_booked_serials.push(serialModel.value[serial._id]);
      }
    }
  }

  booked_serials.value = temp_booked_serials;
};

const cancel = () => {
  initFormData();
  emit('close');
};

const ensureAndSave = (link_data, serial_consumed, parent_serial, child_serial) => {
  if (serial_consumed.value.find((str) => str === child_serial._key)) {
    return false;
  }
  serial_consumed.value.push(child_serial._key);
  link_data.push({
    parent_serial_key: parent_serial._key,
    child_serial_key: child_serial._key,
    wo_key: props.wo_key,
    component_key: component_key.value,
    batch_key: props.batch_key,
    replaced: false,
  });
  return true;
};


/* ================================
            SAVE
================================ */

const save = async () => {
  saving.value = true;

  let link_data = [];
  let serial_consumed = [];
  let initial_values = initialValues.value;
  for (const parent_serial of batch_serials.value) {
    if (serialModel.value[parent_serial._id]) {
      if (Array.isArray(serialModel.value[parent_serial._id])) {
        for (const child_serial of serialModel.value[parent_serial._id]) {
          if (
            !ensureAndSave(
              link_data,
              serial_consumed,
              parent_serial,
              child_serial,
            )
          ) {
            window.alert($t('serial_field.component_reused'));
            saving.value = false;
            return;
          }
        }
      } else {
        if (
          !ensureAndSave(
            link_data,
            serial_consumed,
            parent_serial,
            serialModel.value[parent_serial._id],
          )
        ) {
          window.alert($t('serial_field.component_reused'));
          saving.value = false;
          return;
        }
      }
    }
  }

  for (const inital_data of initial_values) {
    const found = link_data.some(
      (el) =>
        el.parent_serial_key === inital_data.parent_serial_key &&
        el.child_serial_key === inital_data.child_serial_key,
    );
    if (!found) {
      let reason =
        replace_serials_reason.value['Serial/' + inital_data.parent_serial_key];
      if (!reason) {
        window.alert($t('serial_field.missing_reason'));
        saving.value = false;
        return;
      }

      link_data.push({
        ...inital_data,
        reason: reason,
      });
    }
  }

  const event = {
    event_type: 'SERIAL_LINKED',
    user_key: session_data.value.session_key,
    timestamp: timestamp(),
    wo_key: props.wo_key,
    batch_key: props.batch_key,
  };
  for (const link of link_data) {
    await api.post('event', {
      ...event,
      ...link,
    });
  }
  saving.value = false;
  emit('close');
};

// Watch
watch(() => props.show, () => {
  initFormData();
  if (!props.show) {return};
  if (props.traceability_enabled) {
    getBatchSerials();
  } else {
    fakeBatchSerials();
  }
});
</script>
