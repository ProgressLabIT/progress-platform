<template>
  <BaseModalScreen
    :show="show"
    @close="$emit('close')"
    no_esc_dismiss>

      <template #header>
        <div class="q-ml-md display highlight weight-medium col ">
          TEMPLATE: {{ working_template.name }}
        </div>
      </template>

      <template #content>
        <div id="pdf-designer" class="absolute-full" />

        <!-- ACTION MENU -->
        <div class="absolute-bottom-left q-ml-md q-mb-md">
          <q-list>
            <q-item clickable v-ripple @click="show_rename=true">
              <q-item-section side>
                <q-icon name="mdi-pencil" />
              </q-item-section>
              <q-item-section class="display weight-bold">
                RENAME
              </q-item-section>
            </q-item>
            <q-item clickable v-ripple @click="$refs.upload_pdf.click()">
              <q-item-section side>
                <q-icon name="mdi-upload" />
              </q-item-section>
              <q-item-section class="display weight-bold">
                UPLOAD PDF
              </q-item-section>
            </q-item>
            <q-item clickable v-ripple v-if="hasChanged" @click="saveTemplate">
              <q-item-section side>
                <q-icon name="mdi-database-check" />
              </q-item-section>
              <q-item-section class="display weight-bold">
                SAVE
              </q-item-section>
            </q-item>
          </q-list>
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
            <q-input filled v-model="name" />
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
      original_template: undefined,
      working_template: null,
      show_rename: false
    }
  },

  computed: {
    hasChanged() {
      return isEqual(this.original_template, this.working_template)
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
        this.template.basePdf = reader.result
        this.initDesigner()
      }
    },

    saveTemplate () {
      const newTemplate = this.designer.getTemplate()
      console.log(newTemplate)
      if (this.mode == 'new') {
        this.$api.post('print-template', {
          name: this.name,
          template: newTemplate
        }).then(() => {
          this.$emit('saved')
          // this.closeDesigner()
        })
      }
    },

    initDesigner () {
      const container = document.getElementById('pdf-designer')
      this.designer = new Designer({
        domContainer: container,
        template: this.working_template.template
      })
    },

    closeDesigner() {
      // TODO: Add alert if changes haven't been saved
      this.template = null
      this.$emit('close')
    },

    initTemplate() {
      const template = this.edit_template ?? {
        name: this.$t('print_template_new'),
        template: {
          basePdf: BLANK_PDF,
          schemas: []
        }
      }
      this.original_template = cloneDeep(template)
      this.working_template = cloneDeep(template)
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
