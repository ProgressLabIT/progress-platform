<template>
  <div class="col column q-pt-xl q-px-xl">
    <div class="col-auto row">
      <div class="col">
        <div class="text-h3 q-px-none q-pt-none nowrap">
          {{ step.title }}
        </div>
        <div class="text-body2 text-low" style="white-space: pre-line;">
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
          :disable="!isJobActive || batchStep?.done"
          :root-path="`/media/step/${step._key}`"
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
});

const store = useStore();

const batchStep = computed(() => store.getters.getBatchStep(props.step._key));

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

const formData = computed(() => batchStep.value?.form_data ?? []);
const formDataIndexByFieldKey = computed(() => {
  const indexByKey = {};
  formData.value.forEach(({ form_field_key }, index) => {
    indexByKey[form_field_key] = index;
  });
  return indexByKey;
});
function updateField(field, value) {
  store.commit('UPDATE_STEP_FORM_DATA', {
    stepKey: props.step._key,
    index: formDataIndexByFieldKey.value[field._key],
    data: {
      form_field_key: field._key,
      custom_field_key: field.custom_field_key,
      value,
    },
  });
}

const isJobActive = computed(
  () => store.state.traceability.working_job_data.active,
);

const { open: openPrintDialog, isAvailable } = usePrintDialog({
  context: 'step',
  contextData: props.step,
});
</script>
