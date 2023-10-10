<template>
  <q-card
    square
    bordered
    class="surface2">
    <q-card-section class="row items-baseline">
      <q-icon
        class=""
        name="mdi-file-document"
        size="sm">
      </q-icon>
      <div class="q-ml-sm text-h3" :class="{ 'text-italic': template.temp}">
        <div>{{ template.name }}</div>
        <div v-if="template.temp" class="smaller">({{ $capitalize($t('unsaved')) }})</div>
      </div>
    </q-card-section>
    <q-card-section>
      {{ template.description }}
    </q-card-section>
    <q-card-section class="row justify-start q-gutter-sm">
      <q-btn
        size="sm"
        flat
        round
        @click="showTemplatePreview"
        icon="mdi-file-search-outline">
      </q-btn>
      <q-btn
        v-if="allow_edit"
        flat
        round
        size="sm"
        @click="editTemplate"
        icon="mdi-pencil">
      </q-btn>
      <!-- TODO: Implement delete method -->
      <q-btn
        v-if="allow_delete"
        flat
        round
        size="sm"
        @click="$emit('delete')"
        icon="mdi-delete">
      </q-btn>
    </q-card-section>

    <PrintTemplateDesigner
      :show="edit_template != null"
      :edit_template="edit_template"
      @close="resetDesigner"
      @saved="$emit('saved')">
    </PrintTemplateDesigner>

     <!-- PRINT FORM/PREVIEW -->
    <MediaViewer
      :show="!!show_preview"
      :media_name="show_preview?.name"
      :media_src="show_preview?.pdf"
      @close="show_preview = null">
    </MediaViewer>
  </q-card>
</template>

<script>
import { generate } from '@pdfme/generator'
import MediaViewer from '@/components/MediaViewer.vue'
import PrintTemplateDesigner from '@/components/PrintTemplateDesigner.vue'


export default {

  name: 'PrintTemplateCard',

  components: {
    MediaViewer,
    PrintTemplateDesigner
  },

  props: {
    template: {
      type: Object,
      required: true
    },

    allow_edit: {
      type: Boolean,
      default: false
    },

    allow_delete: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      show_preview: false,
      edit_template: null
    }
  },

  methods: {
    async showTemplatePreview() {
      const { data: { template } } = await this.$api.get(`print-template/${this.template._key}`)
      const inputs = template.sampledata
      this.show_preview = {
        name: template.name,
        pdf: await generate({ template, inputs })
      }
    },

    editTemplate(template_key) {
      this.$api.get(`print-template/${this.template._key}`).then(resp =>{
        this.edit_template = resp.data
        this.show_designer = true
      })
    },

    resetDesigner() {
      this.show_designer = false
      this.edit_template =null
    }

  }
}
</script>

<style lang="css" scoped>
</style>
