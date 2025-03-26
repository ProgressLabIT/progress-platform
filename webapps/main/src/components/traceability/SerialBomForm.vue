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
              {{ t('serial') + ' #' + serial_labels[index] }}
            </div>
            <div
              v-if="!batch_serials[index]?.code ?? false"
              class="text-italic text-body2 q-ml-md text-low"
            >
              (TEMP ID)
            </div>
          </div>
        </q-card-section>

        <NoDataAlert v-if="!bom_components">
          {{ t('serial_field.noData') }}
        </NoDataAlert>

        <q-card-section v-else class="column q-gutter-y-md">
          <template
            v-for="component in bom_components.filter(c => c.traceability_level !== null)"
            :key="component.component_key"
          >
            <div class="row q-mb-md">
              <div class="col">
                <BaseAutocompleteSerial
                  v-if="component.traceability_level !== null"
                  v-model="
                    serialModel[getComponentLineKey(component.component_key)]
                  "
                  :initial_values="
                    initalModel[getComponentLineKey(component.component_key)]
                  "
                  :label="
                    $capitalize([t('serial'), component.component_code, '-', component.component_description].join(' '))
                  "
                  :hint="t('serial_autocomplete_hint', { minChars: 3 })"
                  :loading="loading"
                  :product_key="component.component_key"
                  :can_create="true"
                  :selection_qt="qt[component.component_key]"
                  :filter_used="true"
                  :filtered_values="booked_serials[component.component_key]"
                  :disable="
                    ((serialModel[getComponentLineKey(component.component_key)]
                      ?.length >= qt[component.component_key] ||
                      (qt[component.component_key] === 1 &&
                        serialModel[getComponentLineKey(component.component_key)]
                          ?._key)) &&
                      !replace_serials[
                        getComponentLineKey(component.component_key)
                      ]) ||
                    phase_key !== component.phase_key
                  "
                  @select="
                    (selection) =>
                      onSerialSelection(
                        selection,
                        component.component_key,
                        getComponentLineKey(component.component_key),
                      )
                  "
                >
                </BaseAutocompleteSerial>
              </div>
              <div
                v-if="
                  component.traceability_level !== null &&
                  !replace_serials[getComponentLineKey(component.component_key)]
                "
                class="col-auto q-ml-md"
              >
                <q-btn
                  flat
                  round
                  icon="mdi-pencil"
                  :disable="phase_key !== component.phase_key"
                  @click="
                    replace_serials[getComponentLineKey(component.component_key)] =
                      true
                  "
                />
              </div>
            </div>

            <q-input
              class="q-mt-sm"
              label="Ragione della modifica"
              v-if="
                replace_serials[getComponentLineKey(component.component_key)] &&
                phase_key === component.phase_key
              "
              v-model="
                replace_serials_reason[
                  getComponentLineKey(component.component_key)
                ]
              "
              filled
            />
            <q-separator class="q-my-md" />
          </template>
        </q-card-section>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <template v-if="batch_serials.length > 1">
              <q-btn
                v-if="index > 0"
                icon="mdi-arrow-left-bold"
                color="theme-blue"
                @click="index = index - 1"
              >
              </q-btn>
              <q-btn
                v-if="index < batch_serials.length - 1"
                icon="mdi-arrow-right-bold"
                color="theme-blue"
                @click="index = index + 1"
              >
              </q-btn>
            </template>
            <q-btn
              v-if="batch_serials"
              color="theme-orange"
              :label="t('save')"
              :loading="saving"
              @click="
                () => {
                  save();
                }
              "
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
import { useStore } from 'vuex';
import { useI18n } from 'vue-i18n';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import NoDataAlert from '@/components/NoDataAlert.vue';
import { timestamp } from '@/lib/TimeHandling.js';
import { api } from '@/boot/axios';
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
  wo_key: {
    type: String,
    required: true,
  },
  phase_key: {
    type: String,
    required: true,
  },
  bom_components: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['close']);
const store = useStore();
const { t } = useI18n();

const saving = ref(false);
const enableSave = ref(false);
const serialModel = ref([]);
const initalModel = ref([]);
const qt = ref([]);
const initialValues = ref([]);
const serial_ids = ref([]);
const serial_labels = ref([]);
const batch_serials = ref([]);
const replace_serials = ref([]);
const booked_serials = ref([]);
const replace_serials_reason = ref([]);
const loading = ref(false);
const index = ref(0);

const faked_batch_serials = computed(() => store.state.traceability.current_batch_faked_serials);
const session_data = computed(() => store.state.session);

const getComponentLineKey = (component_key) => {
  return [serial_ids.value[index.value], component_key].join(' ');
};

const getBatchSerials = async () => {
  loading.value = true;
  const { data: batch_serials_data } = await api.get('serial-batch', {
    params: {
      batch_key: props.batch_key,
    },
  });

  batch_serials.value = batch_serials_data;
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

const initFormData = async () => {
  saving.value = false;
  enableSave.value = false;
};

const fillInitialData = () => {
  serialModel.value = [];
  initalModel.value = [];
  initialValues.value = [];
  serial_ids.value = [];
  qt.value = [];
  replace_serials.value = [];
  booked_serials.value = [];

  for (const component of props.bom_components) {
    if (props.traceability_enabled) {
      qt.value[component.component_key] = component.qt;
    } else {
      qt.value[component.component_key] = component.batch_qt;
    }
  }

  for (const serial of batch_serials.value) {
    serial_ids.value.push(serial._id);
    serial_labels.value.push(serial?.code || serial._key);

    for (const component of props.bom_components) {
      const key = [serial._id, component.component_key].join(' ');
      if (!serialModel.value[key]) {
        serialModel.value[key] = [];
        initalModel.value[key] = [];
        replace_serials.value[key] = false;
        replace_serials_reason.value[key] = null;
      }
    }

    for (const child of serial.children) {
      const key = [serial._id, child.product_key].join(' ');
      if (!serialModel.value[key]) {
        serialModel.value[key] = [];
        initalModel.value[key] = [];
        replace_serials.value[key] = false;
        replace_serials_reason.value[key] = null;
      }

      let serial_link = {
        _key: child._key,
        label: child.code,
        product_key: child.product_key,
        wo_key: child.wo_key,
        value: child._key,
      };

      if (qt.value[child.product_key] > 1) {
        serialModel.value[key].push(serial_link);
        initalModel.value[key].push(serial_link);
      } else {
        serialModel.value[key] = serial_link;
        initalModel.value[key] = serial_link;
      }

      initialValues.value.push({
        parent_serial_key: serial._key,
        child_serial_key: child._key,
        wo_key: child.wo_key,
        reason: null,
        replaced: true,
        component_key: child.product_key,
        batch_key: props.batch_key,
      });

      if (!booked_serials.value[child.product_key]) {
        booked_serials.value[child.product_key] = [];
      }
      booked_serials.value[child.product_key].push(child.code);
    }
  }
};

const onSerialSelection = (selectedSerials, component_key, selected_key) => {
  let temp_booked_serials = [];

  if (Array.isArray(selectedSerials)) {
    for (const serial of selectedSerials) {
      temp_booked_serials.push(serial.label);
    }
  } else if (selectedSerials) {
    temp_booked_serials.push(selectedSerials.label);
  }

  for (const serial_from of batch_serials.value) {
    for (const component of props.bom_components) {
      if (component?.component_key === component_key) {
        const key = [serial_from._id, component.component_key].join(' ');
        if (serialModel.value[key] && selected_key !== key) {
          if (Array.isArray(serialModel.value[key])) {
            for (const serial_to of serialModel.value[key]) {
              temp_booked_serials.push(serial_to.label);
            }
          } else {
            temp_booked_serials.push(serialModel.value[key].label);
          }
        }
      }
    }
  }
  booked_serials.value[component_key] = temp_booked_serials;
};

const cancel = () => {
  initFormData();
  emit('close');
};

const ensureAndSave = (
  link_data,
  serial_consumed,
  component_key,
  serial_from,
  serial_to,
) => {
  if (serial_consumed.find((str) => str === serial_to._key)) {
    return false;
  }
  serial_consumed.push(serial_to._key);
  link_data.push({
    wo_key: props.wo_key,
    component_key: component_key,
    batch_key: props.batch_key,
    parent_serial_key: serial_from._key,
    child_serial_key: serial_to._key,
    reason: null,
    replaced: false,
  });
  return true;
};

const save = async () => {
  saving.value = true;

  let link_data = [];
  let initial_values = initialValues.value;
  let serial_consumed = [];

  for (const serial_from of batch_serials.value) {
    for (const component of props.bom_components) {
      const key = [serial_from._id, component.component_key].join(' ');
      if (serialModel.value[key]) {
        if (Array.isArray(serialModel.value[key])) {
          for (const serial_to of serialModel.value[key]) {
            if (
              !ensureAndSave(
                link_data,
                serial_consumed,
                component.component_key,
                serial_from,
                serial_to,
              )
            ) {
              window.alert(t('serial_field.component_reused'));
              saving.value = false;
              return;
            }
          }
        } else {
          if (
            !ensureAndSave(
              link_data,
              serial_consumed,
              component.component_key,
              serial_from,
              serialModel.value[key],
            )
          ) {
            window.alert(t('serial_field.component_reused'));
            saving.value = false;
            return;
          }
        }
      }
    }
  }

  for (const inital_data of initial_values) {
    const found = link_data.some(
      (el) =>
        el.from_serial === inital_data.from_serial &&
        el.to_serial === inital_data.to_serial,
    );
    if (!found) {
      const serial_key = [
        'Serial/' + inital_data.from_serial,
        inital_data.component_key,
      ].join(' ');
      let reason = replace_serials_reason.value[serial_key];
      if (!reason) {
        window.alert(t('serial_field.missing_reason'));
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

watch(() => props.show, (newVal) => {
  index.value = 0;
  initFormData();
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
