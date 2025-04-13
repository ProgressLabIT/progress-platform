<template>
  <div class="col column q-pt-xl q-px-xl">
    <div class="col-auto row">
      <div class="col">
        <div class="text-h3 q-px-none q-pt-none nowrap">
          {{ step.title }}
        </div>
        <div class="text-body2 text-low" style="white-space: pre-line">
          {{ step.description }}
        </div>
      </div>

      <div>
        <q-btn
          v-if="isAvailable"
          color="primary"
          icon="mdi-printer"
          :label="$t('print')"
          @click="openPrintDialog"
        >
          <q-tooltip>{{ $capitalize($t('print')) }}</q-tooltip>
        </q-btn>
      </div>
    </div>

    <q-scroll-area class="col q-mt-lg q-pr-md">
      <div v-for="field in formFields" :key="field._key" class="q-py-xs">
        <FormField
          :field="field"
          :disable="(!isJobActive || batchStep?.done) && !stepEditMode"
          :root-path="`/media/traceability/${work_order_key}/${batch_key}/${step._key}/${field.custom_field_key}/${field._key}`"
          @update="(value) => updateField(field, value)"
        />
      </div>
    </q-scroll-area>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useStore } from 'vuex';
import FormField from '@/components/FormField.vue';
import { usePrintDialog } from '@/lib/print';
import { api } from '@/boot/axios';
import { debounce } from 'lodash';

/**
 * @typedef {{
 * _key: string;
 * title: string;
 * description: string;
 * form_fields: import('@/types/form').FormField[];
 * }} Step
 */

const props = defineProps({
  step: {
    type: /** @type {import('vue').PropType<Step>} */ (Object),
    required: true,
  },
  work_order_key: {
    type: String,
    default: null,
  },
  batch_key: {
    type: String,
    default: null,
  },
  product_key: {
    type: String,
    default: null,
  },
});

const store = useStore();

const batchStep = computed(() => store.getters.getBatchStep(props.step._key));
const batchKey = computed(() => store.state.traceability.current_batch_data._key);
const stepKey = computed(() => props.step._key);


// TODO: unify and centralize form data handling with IssueForm
// TODO: add file handling like in IssueForm

const formFields = computed(() =>
  props.step.form_fields.map((field) => {
    const index = formDataIndexByFieldKey.value[field._key];
    return {
      ...field,
      value: formData.value[index]?.value,
    };
  }),
);

const stepEditMode = computed(() => store.getters.isCurrentStepEditMode());

const formData = computed(() => batchStep.value?.form_data ?? []);
const formDataIndexByFieldKey = computed(() => {
  const indexByKey = {};
  formData.value.forEach(({ form_field_key }, index) => {
    indexByKey[form_field_key] = index;
  });
  return indexByKey;
});

const updateField = debounce((field, value) => {
  store.commit('UPDATE_STEP_FORM_DATA', {
    stepKey: props.step._key,
    index: formDataIndexByFieldKey.value[field._key],
    data: {
      form_field_key: field._key,
      custom_field_key: field.custom_field_key,
      value,
    },
  });
  // Do not autosave with step already marked as done, i.e. during step edit
  if (batchStep.value?.status !== 'done') {
    api.post(`batch/temp-data`, {
      execution_record_key: batchStep.value?.execution_record_key,
      step_key: stepKey.value,
      batch_key: batchKey.value,
      form_data: formData.value,
    }).then(({ data }) => {
      store.commit('SET_STEP_EXECUTION_KEY', {
        stepKey: stepKey.value,
        executionRecordKey: data.detail.execution_record_key,
      });
    });
  }
}, 500);

const isJobActive = computed(
  () => store.state.traceability.working_job_data.active,
);

const { open: openPrintDialog, isAvailable } = usePrintDialog({
  context: 'step',
  contextData: {
    ...props.step,
    work_order_key: props.work_order_key,
    batch_key: props.batch_key,
    product_key: props.product_key,
  },
});
</script>
