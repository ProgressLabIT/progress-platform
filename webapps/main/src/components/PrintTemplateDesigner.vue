<template>
  <BaseModalScreen :show="show" no-esc-dismiss @close="$emit('close')">
    <template #header>
      <div class="q-ml-md display highlight weight-medium col">
        {{ $capitalize($t('print_template')) }}
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

          <div class="text-h5 q-mt-lg">{{ $capitalize($t('link', 2)) }}</div>
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
            :label="$t('print_template_load_pdf')"
            color="primary"
            icon="mdi-upload"
            @click="$refs.pdfFileInput.click()"
          />

          <q-btn
            :label="$t('save')"
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

      <!-- TODO: Implement -->
      <BaseDialog :show="showRename">
        <BaseActionCard
          :title="$capitalize($t('print_template_rename'))"
          :save-label="$t('confirm')"
          @cancel="cancelRename"
          @save="showRename = false"
        />
      </BaseDialog>
    </template>
  </BaseModalScreen>
</template>

<script setup>
import { Designer, BLANK_PDF } from '@pdfme/ui';
import { cloneDeep } from 'lodash';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { api } from '@/boot/axios';
import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseModalScreen from '@/components/BaseModalScreen.vue';

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  editTemplate: {
    type: Object,
    default: undefined,
  },
});

const emit = defineEmits(['close', 'saved']);

watch(
  () => props.show,
  (show) => {
    if (show) {
      initTemplate();
      setTimeout(initDesigner, 500);
    }
  },
);

const templateDataOptions = [
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
];

const { t, locale } = useI18n();
const emptyTemplate = computed(() => ({
  name: t('print_template_new'),
  description: undefined,
  presets: {},
  template: {
    basePdf: BLANK_PDF,
    schemas: [],
  },
}));

const mode = ref();
const workingTemplate = ref();

/** @type {Designer} */
let designer;
function initDesigner() {
  const container = document.getElementById('pdf-designer');
  designer = new Designer({
    domContainer: container,
    template: workingTemplate.value.template,
    options: { lang: locale.value },
  });
  designer.onChangeTemplate((template) => {
    workingTemplate.value.template = cloneDeep(template);
  });
}
function closeDesigner() {
  // TODO: Add alert if changes haven't been saved
  designer.destroy();
  workingTemplate.value = undefined;
  emit('close');
}
async function uploadPdf(file) {
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = () => {
    workingTemplate.value.template.basePdf = reader.result;
    initDesigner();
  };
}

function initTemplate() {
  if (props.editTemplate) {
    mode.value = 'edit';
    workingTemplate.value = cloneDeep(props.editTemplate);
  } else {
    mode.value = 'new';
    workingTemplate.value = emptyTemplate.value;
  }
}

async function saveTemplate() {
  await api.request({
    method: mode.value === 'new' ? 'POST' : 'PUT',
    url: 'print-template',
    data: {
      ...workingTemplate.value,
      template: designer.getTemplate(),
    },
  });
  emit('saved');
  closeDesigner();
}

const showRename = ref(false);
function cancelRename() {
  // TODO: Reset name
  showRename.value = false;
}
</script>
