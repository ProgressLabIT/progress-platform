<template>
  <div class="column">
    <div class="text-h5 text-uppercase q-mt-xl q-mb-md">
      {{ $t('phase.form_title') }}
    </div>

    <FormTemplateEditor
      v-model="step.form_fields"
      :edit-mode="editMode"
    />
  </div>
</template>

<script setup>
import { watch } from 'vue'
import FormTemplateEditor from '@/components/FormTemplateEditor.vue'

defineProps({
  editMode: {
    type: Boolean,
    required: true
  }
})

const stepModel = defineModel('step', { type: Object })
// FIXME: _key points to CustomField, we should join the data to get extra data like `type`
// TODO: Migrate the data, and ensure the server returns an empty array
watch(
  stepModel,
  (step) => {
    if (!step.form_fields) {
      step.form_fields = []
    }
  },
  { immediate: true }
)
</script>
