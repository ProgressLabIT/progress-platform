<template>
  <BaseDialog :show="show" @close.stop="cancel">
    <q-card
      square
      class="surface1 q-pa-md"
      style="min-width: 600px; max-width: 800px"
    >
      <q-form ref="issue-form">
        <!-- FORM TITLE -->
        <q-card-section>
          <div class="row justify-between items-center">
            <div class="text-h2 display highlight text-center">
              <template v-if="mode === 'new'">
                {{ $t('issue_new_title') }}
              </template>
              <template v-else>
                {{ $t('issue_update_title') }}
              </template>
            </div>
          </div>
        </q-card-section>

        <!-- FORM BODY -->

        <!-- ISSUE LINKS -->
        <q-card-section
          v-if="mode === 'new' && with_links && form_step === 'links'"
          class="column q-gutter-md"
        >
          <!-- "Path" selection (WorkOrder, Product, Serial, General...) -->
          <q-select
            :options="link_form_options"
            filled
            clearable
            emit-value
            map-options
            :model-value="link_form"
            :label="$t('issue_new_link_type_label')"
            @update:model-value="updateLinkForm"
          />

          <!-- SERIAL -->
          <BaseAutocompleteSerial
            v-if="link_form === 'serial'"
            v-model="links.serial"
            :initial_values="links.serial"
            :label="$capitalize($t('serial'))"
            :hint="$t('serial_autocomplete_hint', { minChars: 3 })"
            @select="(selection) => loadSerial(selection)"
          >
          </BaseAutocompleteSerial>

          <!-- WORK ORDER -->
          <BaseAutocompleteWorkOrder
            v-if="link_form === 'order'"
            :value="links.work_order"
            :label="$capitalize($t('work_order.long'))"
            @select="(selection) => loadWorkOrder(selection)"
          />

          <!-- PRODUCT -->
          <BaseAutocompleteProduct
            v-if="link_form === 'product'"
            :value="links.product"
            :hint="
              (links.work_order || links.product) && !phase_data
                ? $t('phase.no_phase')
                : null
            "
            key-only
            :label="$capitalize($t('product.label'))"
            @select="(selection) => loadProduct(selection)"
          />

          <!-- PHASE -->
          <q-select
            v-if="phase_data && !links.serial"
            :model-value="links.phase"
            :label="$t('phase.short')"
            filled
            clearable
            :options="phase_data"
            option-label="alias"
            @update:model-value="(selection) => loadPhase(selection)"
          />

          <!-- JOB -->
          <q-select
            v-if="link_form === 'order' && links.phase"
            v-model="links.job"
            :label="$capitalize($t('job.label'))"
            filled
            clearable
            :options="phase_jobs"
          >
            <template #option="scope">
              <JobListItem
                v-bind="scope.itemProps"
                :job-data="scope.opt"
                show-progress
                show-assignee
              />
            </template>
            <template #selected-item="scope">
              <JobListItem :job-data="scope.opt" />
            </template>
          </q-select>

          <template v-if="link_form === 'general'">
            <BaseAutocompleteUser
              v-model="links.user"
              :label="$t('user.label')"
            >
            </BaseAutocompleteUser>
            <BaseAutocompleteOperation
              v-model="links.operation"
              :label="$capitalize($t('operation.label'))"
            >
            </BaseAutocompleteOperation>
          </template>
        </q-card-section>

        <!-- ISSUE DATA -->
        <div v-else key="issue_data">
          <!-- ISSUE TYPE SELECTION -->
          <q-card-section>
            <BaseAutocompleteIssueType
              :value="issue_type"
              @select="(value) => setIssueType(value)"
            />
          </q-card-section>

          <!-- FORM FIELDS -->
          <q-card-section>
            <template v-if="issue_type">
              <FormField
                v-for="field in form_fields"
                :key="field._key"
                :field="field"
                :root-path="`/media/issue/${issue?._key}/${field._key}`"
                class="q-mb-lg"
                @update="field.value = $event"
              />
            </template>
          </q-card-section>
        </div>

        <!-- FORM ACTIONS -->
        <q-card-section>
          <div class="row q-gutter-md">
            <q-btn
              v-if="mode === 'new' && with_links && form_step === 'links'"
              color="theme-blue"
              :label="$t('next')"
              @click="form_step = 'data'"
            >
            </q-btn>
            <template v-else>
              <q-btn
                v-if="with_links"
                icon="mdi-arrow-left-bold"
                color="theme-blue"
                @click="form_step = 'links'"
              >
              </q-btn>
              <q-btn
                v-if="!critical_only"
                color="theme-orange"
                :label="$t('save')"
                :loading="saving"
                @click="
                  () => {
                    critical = false;
                    save();
                  }
                "
              >
              </q-btn>
              <q-btn
                color="theme-red"
                @click="
                  () => {
                    critical = true;
                    save();
                  }
                "
              >
                {{ $t('save') }} {{ $t('critical') }}
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
import BaseAutocompleteIssueType from '@/components/BaseAutocompleteIssueType.vue';
import BaseAutocompleteOperation from '@/components/BaseAutocompleteOperation.vue';
import BaseAutocompleteProduct from '@/components/BaseAutocompleteProduct.vue';
import BaseAutocompleteSerial from '@/components/BaseAutocompleteSerial.vue';
import BaseAutocompleteUser from '@/components/BaseAutocompleteUser.vue';
import BaseAutocompleteWorkOrder from '@/components/BaseAutocompleteWorkOrder.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import FormField from '@/components/FormField.vue';
import JobListItem from '@/components/JobListItem.vue';
import { sendEvent } from '@/composables/event.js';

const props = defineProps({
  show: {
    type: Boolean,
    default: true,
  },
  mode: {
    type: String,
    default: 'new',
  },
  issue: {
    type: Object,
    default: undefined,
  },
  with_links: {
    type: Boolean,
    default: false,
  },
  auto_link_mode: {
    type: String,
    default: undefined,
    validator: (value) => ['work_order', 'work_session'].includes(value),
  },
  auto_links: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['close', 'issueCreated', 'cancel']);

// Composables
const store = useStore();
const { t } = useI18n();
const $q = useQuasar();

// Reactive data
const critical_only = ref(false);
const saving = ref(false);
const initalized = ref(false);
const issue_type = ref(null);
const form_step = ref('data');
/** @type {import('@/types/form').FormField[]} */
const form_fields = ref([]);
const critical = ref(false);
const link_form = ref(null);
const phase_data = ref(null);
const phase_jobs = ref(null);
const links = ref({
  product: null,
  operation: null,
  phase: null,
  work_order: null,
  user: null,
  job: null,
  serial: null,
});

// Computed properties
const job_data = computed(() => store.state.traceability.working_job_data);
const session_data = computed(() => store.state.session);
const link_form_options = computed(() => [
  {
    value: 'order',
    label: t('work_order.long'),
  },
  {
    value: 'product',
    label: t('product.label'),
  },
  {
    value: 'serial',
    label: t('serial'),
  },
  {
    value: 'general',
    label: t('general'),
  },
]);

// Methods
function updateLinkForm(value) {
  link_form.value = value;
  initLinks();
}

async function initLinks() {
  // Insert links step if required
  if (props.mode == 'new' && props.with_links) {
    form_step.value = 'links';
  }

  // Reset links
  if (props.with_links) {
    Object.keys(links.value).forEach((l) => (links.value[l] = null));
    phase_data.value = null;
    phase_jobs.value = null;
  }

  // Set auto links if required
  if (
    props.auto_link_mode == 'work_order' &&
    props.auto_links.work_order &&
    !initalized.value
  ) {
    link_form.value = 'order';
    await loadWorkOrder(props.auto_links.work_order);
  }

  if (
    props.auto_link_mode == 'work_session' &&
    props.auto_links &&
    !initalized.value
  ) {
    link_form.value = 'order';
    await loadWorkOrder(props.auto_links.work_order_data);
    if (phase_data.value) {
      let phase = phase_data.value.find(
        (ph) => ph._key === props.auto_links?.phase,
      );
      await loadPhase(phase);
    }
    if (phase_jobs.value) {
      let job = phase_jobs.value.find(
        (j) => j._key === props.auto_links?.job,
      );
      links.value.job = job;
    }
  }
}

function initFormData() {
  const form_template = issue_type.value?.form_template ?? [];

  const use_clean_form =
    props.mode === 'new' ||
    issue_type.value?._key !== props.issue?.issue_type_key;
  if (use_clean_form) {
    // Use fields from issue type template adding empty value
    // If no template, force null, otherwise `undefined` will not be included in the api body and the issue data will not be updated
    form_fields.value = form_template.map((field) => ({
      ...field,
      value: null,
    }));
    return;
  }

  form_fields.value = form_template.map((field) => ({
    ...field,
    value: props.issue.data.find(({ _key }) => _key === field._key)?.value,
  }));
}

function initIssueType() {
  // Fetch issue type data if editing an existing issue
  issue_type.value =
    props.issue?.issue_type_key != null
      ? store.getters.getIssueType(props.issue.issue_type_key)
      : null;
}

function setIssueType(value) {
  issue_type.value = value;
  if (value?.critical) {
    critical_only.value = true;
  } else {
    critical_only.value = false;
  }
}

async function loadSerial(serial) {
  // Set work order data and initialize Phase options to select from
  links.value.serial = serial;
  if (serial?.wo_key) {
    const { data: wo } = await api.get(`work-order/${serial.wo_key}`);
    loadWorkOrder(wo.detail);
  } else {
    loadProduct(serial.product_key);
  }
}

async function loadWorkOrder(wo) {
  // Set work order data and initialize Phase options to select from
  links.value.work_order = wo;
  links.value.product = { _key: wo.product_key };

  let params = new URLSearchParams();
  links.value.work_order?.phase_sequence?.forEach((pk) =>
    params.append('phase_key', pk),
  );

  const { data } = await api.get('phase', { params });
  phase_data.value = data;
}

async function loadProduct(product_key) {
  // To avoid loading in advance a lot of unnecessary product data, the product list contains limited information.
  // So, it is necessary to fetch the full product data first and then load the phases options.
  const { data: product } = await api.get(`product/${product_key}`);
  links.value.product = product;

  if (!product.process_phases) {
    return;
  }

  const params = new URLSearchParams();
  product.process_phases.forEach((phaseKey) =>
    params.append('phase_key', phaseKey),
  );
  const { data: phase } = await api.get('phase', { params });
  phase_data.value = phase;
}

async function loadPhase(phase_data_param) {
  links.value.phase = phase_data_param;
  links.value.operation = { _key: phase_data_param.operation_key };

  // Phase link exists for both order and product mode. Load jobs only in order mode
  if (link_form.value !== 'order') {
    return;
  }

  const { data } = await api.get('job', {
    params: {
      work_order_key: links.value.work_order._key,
      phase_key: links.value.phase._key,
    },
  });
  phase_jobs.value = data.detail;
}

function cancel() {
  initIssueType();
  initFormData();
  initLinks();
  form_step.value = 'links';
  link_form.value = null;
  critical_only.value = false;
  emit('cancel');
}

/**
 * @param {import('@/types/form').FormField} field
 * @returns {string | undefined}
 */
function getFieldType(field) {
  return store.getters.getCustomFieldByKey(field.custom_field_key)?.type;
}

async function saveFiles(issue_key) {
  const promises = form_fields.value
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
        bucket: 'issue',
        object_key: issue_key,
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
  const has_missing_required_fields = form_fields.value
    .filter((f) => f.mandatory)
    .some((f) => {
      const type = store.getters.getCustomFieldByKey(f.custom_field_key).type;
      return type == 'ternary' ? f.value == null : !!f.value == false;
    });

  if (has_missing_required_fields) {
    window.alert(t('fill_mandatory_fields'));
    return;
  }

  saving.value = true;

  const issue_data = {
    issue_type_key: issue_type.value?._key || null,
    critical: critical.value,
    data: form_fields.value.map((field) => ({
      form_field_key: field._key,
      custom_field_key: field.custom_field_key,
      value:
        getFieldType(field) === 'files'
          ? field.value
              ?.filter((file) => !file.delete)
              .map((file) => ({
                size: file.size,
                name: file.name,
              }))
          : field.value,
    })),
  };

  if (props.mode === 'new') {
    // if link is active send data in the form e.g. { type: product, key: whatever }
    issue_data.created_by = `User/${session_data.value.user._key}`; // temporarily hardcoding DB id
    issue_data.close_within = issue_type.value?.close_within ?? 0;

    // Map links to list of objects, including only populated properties
    const linksArray = [];
    Object.entries(links.value).forEach(([key, value]) => {
      if (value) {
        linksArray.push({ type: key, key: value._key });
      }
    });
    issue_data.linked_to = linksArray;
  } else {
    issue_data._key = props.issue._key;
  }

  const message =
    props.mode === 'new' ? 'issue_new_success' : 'issue_update_success';
  const { data } = await sendEvent({
    event_type: props.mode === 'new' ? 'ISSUE_CREATED' : 'ISSUE_UPDATED',
    event_data: { issue_data },
  });
  const issue_key =
    props.mode === 'new' ? data.detail.issue_key : issue_data._key;

  // TODO: Find a way to revert issue creation if file saving doesn't work, or save everything at once via form
  await saveFiles(issue_key);

  // If from work session, fetch issues directly, otherwise signal the parent component to do so
  if (!props.with_links) {
    await store.dispatch('getIssues', {
      work_order_key: job_data.value.wo_key,
    });
  } else {
    emit('issueCreated');
  }
  cancel();
  saving.value = false;
  $q.notify({
    message: t(message),
    color: critical.value ? 'theme-red' : 'theme-orange',
    timeout: 1500,
    position: 'top',
  });
}

// Watchers
watch(
  issue_type,
  () => {
    initFormData();
  },
  { deep: true }
);

watch(
  () => props.show,
  () => {
    initalized.value = false;
    initFormData();
    initLinks();
    initalized.value = true;
  }
);

watch(phase_data, () => {
  // The new list of phases will not contain the selected phase, so reset it
  links.value.phase = null;
});

// Lifecycle
onMounted(() => {
  initIssueType();
  initFormData();
  initLinks();
});
</script>
