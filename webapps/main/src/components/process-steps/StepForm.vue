<template>
  <div class="column">
    <div class="text-h5 text-uppercase q-mt-xl q-mb-md">
      {{ $t('phase.form_title') }}
    </div>

    <FormTemplateEditor v-model="stepModel.form_fields" :edit-mode="editMode" />

    <div class="text-h5 text-uppercase q-mt-xl q-mb-md">
      {{ $t('print_templates') }}
    </div>

    <div
      v-if="stepModel.print_templates.length === 0"
      class="q-mt-md text-italic"
    >
      {{ $t('print_template_none') }}
    </div>
    <div v-else class="col row scroll q-col-gutter-sm">
      <div
        v-for="(template, index) in stepModel.print_templates"
        :key="template._key"
        class="col-3"
      >
        <PrintTemplateCard
          :template="template"
          allow-delete
          @delete="deleteTemplate(index)"
          @restore="template.trash = false"
        />
      </div>
    </div>

    <div class="row">
      <q-btn
        v-if="editMode"
        size="sm"
        color="theme-blue"
        icon="mdi-plus"
        :label="$t('print_template_add')"
        class="q-mt-lg"
        @click="addPrintTemplate"
      />
    </div>
  </div>
</template>

<script setup>
import { Dialog } from 'quasar';
import FormTemplateEditor from '@/components/FormTemplateEditor.vue';
import PrintTemplateCard from '@/components/PrintTemplateCard.vue';
import AddPrintTemplateDialog from './AddPrintTemplateDialog.vue';

defineProps({
  editMode: {
    type: Boolean,
    required: true,
  },
});

const stepModel = defineModel('step', { type: Object });

function addPrintTemplate() {
  Dialog.create({
    component: AddPrintTemplateDialog,
    componentProps: {
      selectedTemplates: stepModel.value.print_templates,
    },
  }).onOk((template) => {
    stepModel.value.print_templates.push({
      ...template,
      temp: true,
    });
  });
}

function deleteTemplate(templateIndex) {
  const template = stepModel.value.print_templates[templateIndex];
  if (template.temp) {
    stepModel.value.print_templates.splice(templateIndex, 1);
  } else {
    template.trash = true;
  }
}
</script>
