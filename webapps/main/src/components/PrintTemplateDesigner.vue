<template>
  <!-- TODO: i18n -->
  <BaseModalScreen :show="show" no-esc-dismiss @close="$emit('close')">
    <template #header>
      <div class="q-ml-md display highlight weight-medium col">
        TEMPLATE
        <span v-if="workingTemplate._key">
          {{ workingTemplate._key }}
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
        style="min-width: 300px"
      >
        <div class="q-gutter-md">
          <q-input
            v-model="workingTemplate.name"
            filled
            :label="$t('name')"
            stack-label
            class="shadow-3"
            input-class="transparent"
          />

          <q-input
            v-model="workingTemplate.description"
            autogrow
            filled
            :label="$t('description')"
            stack-label
            class="shadow-3"
          />

          <div class="text-h5 q-mt-lg">COLLEGAMENTI</div>
          <div v-for="column in workingTemplate.template.columns" :key="column">
            <q-select
              v-model="workingTemplate.presets[column]"
              :options="templateDataOptions"
              :label="column"
              stack-label
              filled
              class="shadow-3"
            />
          </div>

          <q-space />

          <!-- ACTION MENU -->
          <q-btn
            label="UPLOAD PDF"
            color="primary"
            icon="mdi-upload"
            @click="$refs.pdfFileInput.click()"
          />

          <q-btn
            label="SAVE"
            color="primary"
            icon="mdi-database-check"
            @click="saveTemplate"
          />
        </div>
      </div>

      <input
        ref="pdfFileInput"
        type="file"
        accept="application/pdf"
        style="opacity: 0"
        @change="uploadPdf($event.target.files[0])"
      />

      <BaseDialog :show="showRename">
        <BaseActionCard
          title="RINOMINA TEMPLATE"
          :save-label="$t('confirm')"
          @cancel="cancelRename"
          @save="showRename = false"
        />
      </BaseDialog>
    </template>
  </BaseModalScreen>
</template>

<script>
import { Designer, BLANK_PDF } from '@pdfme/ui';
import { cloneDeep } from 'lodash';

import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseModalScreen from '@/components/BaseModalScreen.vue';

export default {
  name: 'PrintTemplateDesigner',

  components: {
    BaseActionCard,
    BaseDialog,
    BaseModalScreen,
  },

  props: {
    show: {
      type: Boolean,
      default: false,
    },
    editTemplate: {
      type: Object,
      default: undefined,
    },
  },

  emits: ['close', 'saved'],

  data() {
    return {
      designer: null,
      showRename: false,
      mode: undefined,
      workingTemplate: undefined,
      templateDataOptions: [
        'current_date',
        'current_time',
        'current_user',
        'job_key',
        'job_qt_planned',
        'job_qt_completed',
        'job_phase_alias',
        'job_start_date',
        'job_start_time',
        'job_end_date',
        'job_end_time',
        'work_order_code',
        'project_code',
        'work_order_qt_planned',
        'work_order_qt_completed',
        'work_order_start_date',
        'work_order_start_time',
        'work_order_end_date',
        'work_order_end_time',
        'product_code',
        'product_description',
        'issue_open_date',
        'issue_open_time',
        'issue_open_user',
        'issue_close_date',
        'issue_close_time',
        'issue_close_user',
        'issue_status',
      ],
    };
  },

  computed: {
    emptyTemplate() {
      return {
        name: this.$t('print_template_new'),
        description: undefined,
        presets: {},
        template: {
          basePdf: BLANK_PDF,
          schemas: [],
        },
      };
    },
  },

  watch: {
    show() {
      if (this.show) {
        this.initTemplate();
        setTimeout(this.initDesigner, 500);
      }
    },
  },

  methods: {
    async uploadPdf(file) {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        this.workingTemplate.template.basePdf = reader.result;
        this.initDesigner();
      };
    },

    async saveTemplate() {
      await this.$api.request({
        method: this.mode === 'new' ? 'POST' : 'PUT',
        url: 'print-template',
        data: {
          ...this.workingTemplate,
          template: this.designer.getTemplate(),
        },
      });
      this.$emit('saved');
      this.closeDesigner();
    },

    initDesigner() {
      const container = document.getElementById('pdf-designer');
      this.designer = new Designer({
        domContainer: container,
        template: this.workingTemplate.template,
        options: { lang: this.$i18n.locale },
      });
      this.designer.onChangeTemplate((template) => {
        this.workingTemplate.template = cloneDeep(template);
      });
    },

    closeDesigner() {
      // TODO: Add alert if changes haven't been saved
      this.designer.destroy();
      this.template = null;
      this.$emit('close');
    },

    initTemplate() {
      if (this.editTemplate) {
        this.mode = 'edit';
        this.workingTemplate = cloneDeep(this.editTemplate);
      } else {
        this.mode = 'new';
        this.workingTemplate = this.emptyTemplate;
      }
    },

    cancelRename() {
      this.initName();
      this.showRename = false;
    },
  },
};
</script>
