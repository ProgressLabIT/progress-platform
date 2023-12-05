<template>
  <div class="col column q-pt-xl q-px-xl">
    <div class="col-auto">
      <div class="text-h3 q-px-none q-pt-none nowrap">
        {{ step.title }}
      </div>
      <div class="text-body2 text-low">
        {{ step.description }}
      </div>
    </div>

    <q-scroll-area class="col q-mt-lg q-pr-md">
      <FormField
        v-for="field in formFields"
        :key="field._key"
        :field_data="field"
        :disable="!isJobActive || batchStep.done"
        :root_path="`/media/step/${step._key}`"
        @update="value => updateField(field, value)"
      />
    </q-scroll-area>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'
import FormField from '@/components/FormField.vue'

const props = defineProps({
  step: {
    type: Object,
    required: true
  }
})

const store = useStore()

const batchStep = computed(() => store.getters.getBatchStep(props.step._key))

// TODO: unify and centralize form data handling with IssueForm
// TODO: add file handling like in IssueForm

const formFields = computed(
  // TODO: migrate the data, and ensure the server returns an empty array
  () => props.step.form_fields?.map(field => {
    const index = formDataIndexByFieldKey.value[field._key]
    return {
      ...field,
      value: formData.value[index]?.value
    }
  }) ?? []
)

// TODO: migrate the data, and ensure the server returns an empty array
const formData = computed(() => batchStep.value.form_data ?? [])
const formDataIndexByFieldKey = computed(() => {
  const indexByKey = {}
  formData.value.forEach(({ form_field_key }, index) => {
    indexByKey[form_field_key] = index
  })
  return indexByKey
})
function updateField(field, value) {
  store.commit('UPDATE_STEP_FORM_DATA', {
    stepKey: props.step._key,
    index: formDataIndexByFieldKey.value[field._key],
    data: {
      form_field_key: field._key,
      value
    }
  })
}

const isJobActive = computed(() => store.state.traceability.working_job_data.active)
</script>
