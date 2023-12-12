<template>
  <div class="fit q-pa-lg column scroll">
    <div
      v-if="templatesModel.length > 0"
      class="row q-col-gutter-md q-ma-none col-auto"
    >
      <div class="col-3"
        v-for="template in templatesModel.filter(template => !('trash' in template))"
        :key="template._key"
      >
        <PrintTemplateCard :template="template" />
      </div>
    </div>
    <div v-else>
      <NoDataAlert />
    </div>

    <q-space />

    <BaseAutocompleteTemplate
      v-if="editMode"
      class="q-px-sm q-mt-md"
      :label="$t('print_template_add')"
      :selected="templatesModel"
      @select="addTemplate"
    />
  </div>
</template>

<script setup>
import NoDataAlert from '@/components/NoDataAlert.vue'
import PrintTemplateCard from '@/components/PrintTemplateCard.vue'
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue'

const props = defineProps({
  editMode: {
    type: Boolean,
    required: true
  }
})

const templatesModel = defineModel({ type: Array })

function addTemplate(template) {
  templatesModel.value.push({
    ...template,
    temp: true,
  })
}

// TODO: Implement delete functionality
/*
function deleteTemplate(index) {
  if (templatesModel.value[index].temp) {
    templatesModel.value.splice(index, 1)
  } else {
    templatesModel.value[index].trash = true
  }
}
*/
</script>
