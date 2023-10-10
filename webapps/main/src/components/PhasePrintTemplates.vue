<template>
  <div class="fit q-pa-lg column scroll">

    <div
      v-if="phase.print_templates.length"
      class="row q-col-gutter-md q-ma-none col-auto">
      <div class="col-3"
        v-for="template in phase.print_templates.filter(t => !('trash' in t))"
        :key="template._key">
        <q-card
          square
          bordered
          class="surface2"
          :class="{ 'text-italic': template.temp }">
          <q-card-section >
            <div class="text-h3 row items-end">
            <q-icon
              class=""
              name="mdi-file-document"
              size="sm">
            </q-icon>
            <div class="q-ml-sm">
              <span>{{ template.name }}</span>
              <span class="q-ml-xs">{{ template.temp ? '(' + $capitalize($t('unsaved')) + ')' : '' }}</span>
            </div>
          </div>
          <div class="q-mt-sm">
            {{ template.description }}
          </div>
          </q-card-section>
          <q-card-section class="row justify-end">
            <q-btn
              size="sm"
              @click="showTemplatePreview(template)"
              :label="$t('preview')"
              color="theme-blue">
            </q-btn>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <v-else>
      <NoDataAlert />
    </v-else>

    <q-space></q-space>

    <BaseAutocompleteTemplate
      v-if="edit_mode"
      class="q-px-sm q-mt-md"
      :label="$t('print_template_add')"
      @select="addTemplate"
      :selected="phase.print_templates">
    </BaseAutocompleteTemplate>

    <MediaViewer
      :show="show_template != null"
      :media_name="show_template?.name"
      :media_src="show_template?.pdf"
      @close="show_template = null">
    </MediaViewer>


  </div>
</template>

<script>
import { generate } from '@pdfme/generator'

import LoadingSignal from '@/components/LoadingSignal.vue'
import MediaViewer from '@/components/MediaViewer.vue'
import NoDataAlert from '@/components/NoDataAlert.vue'
import PrintTemplateDesigner from '@/components/PrintTemplateDesigner.vue'
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue'

export default {
  name: 'PrintTemplateLibrary',

  components: {
    BaseAutocompleteTemplate,
    LoadingSignal,
    MediaViewer,
    NoDataAlert,
    PrintTemplateDesigner
  },

  props: {
    phase: {
      type: Object,
      required: true
    },

    product_data: {
      type: Object,
      required: true
    },

    edit_mode: {
      type: Boolean
    }
  },

  data () {
    return {
      template_list: [],
      show_template: null
    }
  },

  computed: {
    current_phase_index() {
      return this.product_data.last_phase
    }
  },

  methods: {

    addTemplate(selection) {
      this.$store.commit('ADD_TEMP_PHASE_TEMPLATE', {
        phase_index: this.current_phase_index,
        template: selection
      })
    },

    deleteTemplate(index) {
      this.$store.commit('DELETE_TEMP_PHASE_TEMPLATE', {
        phase_index: this.current_phase_index,
        template_index: index
      })
    },

    async showTemplatePreview(t) {
      const { data: { template } } = await this.$api.get(`print-template/${t._key}`)
      const inputs = template.sampledata
      this.show_template = {
        name: t.name,
        pdf: await generate({ template, inputs })
      }
    },
  },
}

</script>
<style lang="sass">

</style>
