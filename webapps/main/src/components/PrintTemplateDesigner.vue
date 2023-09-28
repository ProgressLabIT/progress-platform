<template>
  <BaseModalScreen
    :show="show"
    @close="$emit('close')"
    no_esc_dismiss>

      <template #header>
        <div class="q-ml-md display highlight weight-medium col ">
          TEMPLATE
          <span v-if="working_template._key">
            {{ working_template._key }}
          </span>
          <span v-else>
            {{ $t('new') }}
          </span>
        </div>
      </template>

      <template #content>
        <div id="pdf-designer" class="absolute-full" />

        <div
          class="absolute-top-left full-height scroll q-pa-md"
          style="min-width: 300px;">
          <div class="q-gutter-md">
            <q-input
              filled
              :label="$t('name')"
              stack-label
              class="shadow-3"
              input-class="transparent"
              v-model="working_template.name">
            </q-input>
            <q-input
              filled
              class="shadow-3"
              stack-label
              :label="$t('description')"
              autogrow
              v-model="working_template.description">
            </q-input>

            <div class="text-h5 q-mt-lg">
              COLLEGAMENTI
            </div>
            <div v-for="f in working_template.template.columns">
              <q-select
                :label="f"
                stack-label
                class="shadow-3"
                filled
                :options="template_data_options"
                v-model="template_data_links[f]">
              </q-select>
            </div>

            <q-space></q-space>
            <!-- ACTION MENU -->
            <q-btn
              color="primary"
              icon="mdi-upload"
              label="UPLOAD PDF"
              @click="$refs.upload_pdf.click()">
            </q-btn>

            <q-btn
              color="primary"
              icon="mdi-database-check"
              label="SAVE"
              @click="saveTemplate">
            </q-btn>
          </div>
        </div>


        <input
          ref="upload_pdf"
          type='file'
          accept="application/pdf"
          @change="uploadPdf($event.target.files[0])"
          style="opacity: 0"/>

        <BaseDialog :show="show_rename">
          <BaseActionCard
            @cancel="cancelRename"
            @save="show_rename=false"
            :save_label="$t('confirm')"
            title="RINOMINA TEMPLATE">

          </BaseActionCard>
        </BaseDialog>
      </template>

    </BaseModalScreen>
</template>

<script>
import { Designer, BLANK_PDF } from '@pdfme/ui'
import { cloneDeep, isEqual } from 'lodash'

import BaseModalScreen from '@/components/BaseModalScreen.vue'
import BaseActionCard from '@/components/BaseActionCard.vue'
import BaseDialog from '@/components/BaseDialog.vue'
import LoadingSignal from '@/components/LoadingSignal.vue'

export default {

  name: 'PrintTemplateDesigner',

  components: {
    BaseActionCard,
    BaseDialog,
    BaseModalScreen
  },

  props: {
    show: {
      type: Boolean,
      default: false
    },
    edit_template: {
      type: Object,
    }
  },

  data () {
    return {
      designer: null,
      show_rename: false,
      mode: undefined,
      working_template: undefined,
      template_data_options: [1,2,3],
      template_data_links: {}
    }
  },

  computed: {
    empty_template() {
      return {
        name: this.$t('print_template_new'),
        description: undefined,
        template: {
          basePdf: BLANK_PDF,
          schemas: []
        }
      }
    },

    has_changed() {
      return isEqual(this.working_template, this.mode == 'new' ? this.empty_template : this.edit_template)
    }
  },

  methods: {
    async generatePdf () {
      const pdf = await generate({ template: this.template, inputs: this.inputs })
      const blob = new Blob([pdf.buffer], { type: 'application/pdf' })
      window.open(URL.createObjectURL(blob))
    },

    async uploadPdf (file) {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = () => {
        this.working_template.template.basePdf = reader.result
        this.initDesigner()
      }
    },

    saveTemplate () {
      const data = {
        ...this.working_template,
        template: this.designer.getTemplate()
      }
      const request = this.mode == 'new'
        ? this.$api.post('print-template', data)
        : this.$api.put('print-template', data)

      request.then(() => {
        this.$emit('saved')
        this.closeDesigner()
      })
    },

    initDesigner () {
      const container = document.getElementById('pdf-designer')
      this.designer = new Designer({
        domContainer: container,
        template: this.working_template.template,
        options: { lang: 'it' }
      })
      this.designer.onChangeTemplate(t => this.working_template.template = cloneDeep(t))
    },

    closeDesigner() {
      // TODO: Add alert if changes haven't been saved
      this.designer.destroy()
      this.template = null
      this.$emit('close')
    },

    initTemplate() {
      if (this.edit_template) {
        this.mode = 'edit'
        this.working_template = cloneDeep(this.edit_template)
      }
      else {
        this.mode = 'new'
        this.working_template = this.empty_template
      }
    },

    cancelRename() {
      this.initName()
      this.show_rename = false
    }
  },

  watch: {
    show() {
      if (this.show) {
        this.initTemplate()
        setTimeout(this.initDesigner, 500)
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>
