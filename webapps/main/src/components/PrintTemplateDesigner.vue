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
          class="absolute-top-left q-mt-sm q-ml-sm col q-gutter-md"
          style="min-width: 300px;">
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
        </div>

        <!-- ACTION MENU -->
        <div class="absolute-bottom-left q-ml-md q-mb-md">
          <q-list>
            <q-item clickable v-ripple @click="$refs.upload_pdf.click()">
              <q-item-section side>
                <q-icon name="mdi-upload" />
              </q-item-section>
              <q-item-section class="display weight-bold">
                UPLOAD PDF
              </q-item-section>
            </q-item>
            <q-item clickable v-ripple @click="saveTemplate">
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
        this.template.basePdf = reader.result
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
        template: this.working_template.template
      })
      this.designer.onChangeTemplate = t => console.log(t)
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
