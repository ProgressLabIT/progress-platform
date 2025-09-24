<template>
  <BaseDialog :show="show" @close="cancel">
    <q-card
      square
      class="surface1 q-pa-md"
      style="min-width: 600px; max-width: 800px"
    >
      <q-form ref="serial-form">
        <!-- FORM TITLE -->
        <q-card-section>
          <div class="row justify-between items-center">
            <div class="text-h2 display highlight text-center">
              {{ $t('serial_new_title') }}
            </div>
          </div>
        </q-card-section>

        <!-- FORM BODY -->

        <!-- form_step === 'select_product' -->
        <q-card-section
          v-if="form_step === 'select_product'"
          class="column q-gutter-md"
        >
          <!-- PRODUCT -->
          <BaseAutocompleteProduct
            :value="links.product"
            :hint="!phase_data ? $t('phase.no_phase') : null"
            :load-data="true"
            :traceability-only="true"
            key-only
            :label="$capitalize($t('product.label'))"
            :disable="force_serial_code !== null"
            @select="(selection) => loadProduct(selection)"
          />

          <q-input
            filled
            :label="$capitalize($t('serial'))"
            :disable="force_serial_code !== null"
            stack-label
            input-class="uppercase"
            :model-value="serial_code"
            @update:model-value="(value) => serial_code = value.toUpperCase()"
          />
        </q-card-section>

        <!-- SERIAL DATA -->
        <q-card-section v-else key="serial_data">
          <!-- FORM FIELDS -->
          <div class="text-h3"></div>

          <q-field
            filled
            :label="$t('phase.phase')"
            stack-label
            disable
            class="q-mb-lg"
          >
            <template #control>
              <div class="self-center full-width no-outline" tabindex="0">
                {{ phase_data[phase_index].alias }}
              </div>
            </template>
          </q-field>

          <q-field
            filled
            :label="$t('phase.step')"
            stack-label
            class="q-mb-lg"
            disable
          >
            <template #control>
              <div class="self-center full-width no-outline" tabindex="0">
                {{ phase_data[phase_index]?.steps[step_index]?.title }}
              </div>
            </template>
          </q-field>

          <FormField
            v-for="field in phase_data[phase_index]?.steps[step_index]
              ?.form_fields"
            :key="field._key"
            :field="field"
            :root-path="`/media/serial/${serial?._key}/${field._key}`"
            class="q-mb-lg"
            @update="field.value = $event"
          />
        </q-card-section>

        <!-- FORM ACTIONS    navigation -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="form_step === 'select_product' && has_fields"
              color="theme-blue"
              :label="$t('next')"
              :disable="!links.product || serial_code === null"
              @click="startSteps()"
            >
            </q-btn>
            <q-btn
              v-if="form_step === 'select_product' && !has_fields"
              color="theme-orange"
              :label="$t('save')"
              :disable="serial_code === null"
              :loading="saving"
              @click="
                () => {
                  save();
                }
              "
            >
            </q-btn>
            <template v-else>
              <q-btn
                v-if="form_step === 'fill_steps_data'"
                icon="mdi-arrow-left-bold"
                color="theme-blue"
                @click="prevTile()"
              >
              </q-btn>
              <q-btn
                v-if="!enableSave && form_step === 'fill_steps_data'"
                icon="mdi-arrow-right-bold"
                color="theme-blue"
                @click="nextTile()"
              >
              </q-btn>

              <q-btn
                v-else-if="enableSave"
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
            </template>

            <q-space />
            <q-btn color="theme-grey" :label="$t('cancel')" @click="cancel">
            </q-btn>
          </div>
        </q-card-section>
      </q-form>
    </q-card>
  </BaseDialog>
</template>

<script setup>
import { useQuasar } from 'quasar';
import { ref, computed, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios.js';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import FormField from '@/components/FormField.vue';
import { timestamp } from '@/lib/TimeHandling.js';

const props = defineProps({
  show: {
    type: Boolean,
    default: true,
  },
  serial: {
    type: Object,
    default: undefined,
  },
  auto_link_product: {
    type: String,
    default: null,
  },
  force_serial_code: {
    type: String,
    default: null,
  }
});

const emit = defineEmits(['close', 'serialCreated']);

// Composables
const store = useStore();
const { t } = useI18n();
const $q = useQuasar();

// Reactive data
const phase_index = ref(0);
const has_fields = ref(true);
const step_index = ref(0);
const saving = ref(false);
const enableSave = ref(false);
const form_step = ref('select_product');
const phase_data = ref(null);
const serial_code = ref(null);
const counter_key = ref(null);
const links = ref({
  product: null,
  user: null,
});

// Computed properties
const session_data = computed(() => store.state.session);

// Methods
function initFormData() {
  saving.value = false;
  enableSave.value = false;
  phase_index.value = 0;
  step_index.value = 0;

  links.value.product = null;

  if (props.auto_link_product != null) {
    loadProduct(props.auto_link_product);
  }

  serial_code.value = null;

  if (props.force_serial_code) {
    serial_code.value = props.force_serial_code;
  }
}

function hasCustomField() {
  try {
    return (
      phase_data.value[phase_index.value].steps[step_index.value].form_fields
        .length > 0
    );
  } catch (error) {
    return false;
  }
}

function startSteps() {
  form_step.value = 'fill_steps_data';
  step_index.value = 0;
  phase_index.value = 0;
  enableSaveButton();
}

function nextTile() {
  if (
    step_index.value <
    phase_data.value[phase_index.value].steps.length - 1
  ) {
    step_index.value++;
  } else {
    if (phase_index.value < phase_data.value.length - 1) {
      step_index.value = 0;
      phase_index.value++;
    }
  }

  enableSaveButton();
}

function enableSaveButton() {
  enableSave.value =
    step_index.value >= phase_data.value[phase_index.value].steps.length - 1 &&
    phase_index.value >= phase_data.value.length - 1;

  if (!enableSave.value && !hasCustomField()) {
    nextTile();
  }
}

function prevTile() {
  enableSave.value = false;
  if (step_index.value > 0) {
    step_index.value--;
  } else if (phase_index.value > 0) {
    phase_index.value--;
    step_index.value = phase_data.value[phase_index.value].steps.length - 1;
  } else {
    form_step.value = 'select_product';
    enableSave.value = !phase_data.value;
  }

  if (
    phase_index.value > 0 &&
    step_index.value > 0 &&
    !hasCustomField()
  ) {
    prevTile();
  }
}

async function loadProduct(product_key) {
  if (product_key === null) {
    links.value.product = null;
    return;
  }
  // To avoid loading in advance a lot of unnecessary product data, the product list contains limited information.
  // So, it is necessary to fetch the full product data first and then load the stepss options.
  const { data: product } = await api.get(`product/${product_key}`);

  links.value.product = product;
  counter_key.value = product.counter_key;

  if (!product.process_phases) {
    return;
  }

  const { data: steps } = await api.get(
    `product/${product_key}/process`,
  );
  phase_data.value = steps;

  let hasCustomField = false;

  if (phase_data.value) {
    phase_data.value.forEach((phase) => {
      if (phase.steps) {
        phase.steps.forEach((step) => {
          if (!hasCustomField) {
            hasCustomField = step.form_fields?.length > 0;
          }
        });
      }
    });
  }

  has_fields.value = hasCustomField;
  phase_index.value = 0;
  step_index.value = 0;
}

function cancel() {
  initFormData();
  form_step.value = 'select_product';
  emit('close');
}

/**
 * @param {import('@/types/form').FormField} field
 * @returns {string | undefined}
 */
function getFieldType(field) {
  return store.getters.getCustomFieldByKey(field.custom_field_key)?.type;
}

function getFormFieldValue(phase_key, step_key, fields) {
  return fields.map((field) => ({
    phase_key: phase_key,
    step_key: step_key,
    form_field_key: field._key,
    custom_field_key: field.custom_field_key,
    label: field.label,
    hint: field.hint,
    mandatory: field.mandatory,
    value:
      getFieldType(field) === 'files'
        ? field.value
            ?.filter((file) => !file.delete)
            .map((file) => ({
              size: file.size,
              name: file.name,
            }))
        : field.value,
  }));
}

function missingMandatoryValues(form_data) {
  let missing_mandatory_fields = false;
  if (!form_data) {
    return missing_mandatory_fields;
  }
  form_data.forEach((field) => {
    let type = getFieldType(field);
    if (
      type !== 'ternary' &&
      field.mandatory &&
      (!field.value || field.value === null || field.value === '')
    ) {
      missing_mandatory_fields = true;
    }
  });
  return missing_mandatory_fields;
}

async function saveFiles(serial_key) {
  let form_fields = [];
  if (phase_data.value) {
    phase_data.value.forEach((phase) => {
      if (phase.steps) {
        phase.steps.forEach((step) => {
          form_fields.push(...step.form_fields);
        });
      }
    });
  }

  const promises = form_fields
    .filter((field) => getFieldType(field) === 'files')
    .map(async (field) => {
      const to_delete = [];
      const to_add = [];

      field.value?.forEach((file) => {
        if (file.temp) {
          to_add.push(file.content);
        } else if (file.delete) {
          to_delete.push(file.name);
        }
      });

      const target = {
        bucket: 'serial',
        object_key: serial_key,
        subfolder: field._key,
      };

      // Upload new files
      if (to_add.length) {
        // Populate form data
        const add_body = new FormData();
        Object.entries(target).forEach(([k, v]) => add_body.append(k, v));
        to_add.forEach((file) => add_body.append('contents', file));
        // Post files
        try {
          await api.post('/files', add_body);
        } catch (error) {
          console.error(error);
          window.alert(error);
        }
      }

      // Delete files
      if (to_delete.length) {
        try {
          await api.delete('/files', {
            data: {
              ...target,
              filenames: to_delete,
            },
          });
        } catch (error) {
          console.error(error);
          window.alert(error);
        }
      }
    });

  return Promise.all(promises);
}

async function save() {
  saving.value = true;

  let missing_mandatory_fields = false;

  if (phase_data.value) {
    phase_data.value.forEach((phase) => {
      if (phase.steps) {
        phase.steps.forEach((step) => {
          missing_mandatory_fields =
            missing_mandatory_fields ||
            missingMandatoryValues(step.form_fields);
        });
      }
    });
  }

  if (missing_mandatory_fields) {
    window.alert(t('fill_mandatory_fields'));
    saving.value = false;
    return;
  }

  let data = [];
  if (phase_data.value) {
    phase_data.value.forEach((phase) => {
      if (phase.steps) {
        phase.steps.forEach((step) => {
          data.push(...getFormFieldValue(
            phase._key,
            step._key,
            step.form_fields ? step.form_fields : [],
          ));
        });
      }
    });
  }

  const event = {
    event_type: 'SERIAL_CREATED',
    user_key: session_data.value.user._key,
    user_session_key: session_data.value.session_key,
    timestamp: timestamp(),
    product_key: links.value.product._key,
    code: serial_code.value,
    counter_key: counter_key.value,
    data
  };

  api.post('event', event).then((resp) => {
    if (resp.status === 200) {
      emit('serialCreated');
      saveFiles(resp?.data?.detail?.serial_key).then(() => {
        cancel();
        saving.value = false;
      });
    } else if (resp.response?.status === 422) {
      let error_message = 'traceability.errors.EXCEPTION';
      switch (resp.response?.data?.detail?.error_type) {
        case 'SerialNotCreatedError':
          error_message = 'traceability.errors.SERIAL_NEW_ERROR';
          break;
        case 'SerialCodeAlreadyPresent':
          error_message = 'traceability.errors.SERIAL_NEW_ALREADY_PRESENT';
          break;
        default:
          break;
      }

      $q.notify({
        message: t(error_message),
        color: 'theme-red',
        timeout: 1500,
        position: 'top',
      });
      cancel();
      saving.value = false;
    }
  });
}

// Watchers
watch(
  () => props.show,
  () => {
    initFormData();
  }
);

// Lifecycle
onMounted(() => {
  initFormData();
});
</script>
