<template>
  <div class="column">
    <div class="text-h5 text-uppercase q-mt-xl q-mb-md">
      {{ $t('phase.form_title') }}
    </div>

    <FormTemplateEditor v-model="stepModel.form_fields" :edit-mode="editMode" />
  </div>
</template>

<script setup>
import FormTemplateEditor from '@/components/FormTemplateEditor.vue';

defineProps({
  editMode: {
    type: Boolean,
    required: true,
  },
});

const stepModel = defineModel('step', { type: Object });
</script>
