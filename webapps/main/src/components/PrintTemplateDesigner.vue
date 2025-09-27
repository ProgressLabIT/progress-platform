<template>
  <BaseModalScreen :show="show" no-esc-dismiss @close="$emit('close')">
    <template #header>
      <div class="q-ml-md display highlight weight-medium col">
        {{ $capitalize($t('print_template')) }}
        <span v-if="workingTemplate?._key">
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
          <fieldset
            v-for="column in workingTemplate.template.columns"
            :key="column"
          >
            <legend class="text-h5 q-px-sm">{{ column }}</legend>

            <div class="row items-center q-mb-sm">
              <span class="q-mr-sm">{{ $t('type') }}:</span>

              <q-btn-toggle
                v-model="workingTemplate.links[column].type"
                :options="linkTypeOptions"
                size="sm"
                no-caps
                @update:model-value="workingTemplate.links[column].value = null"
              />
            </div>

            <q-select
              v-if="workingTemplate.links[column].type === 'preset'"
              v-model="workingTemplate.links[column].value"
              :options="templateDataOptions.sort()"
              filled
              class="shadow-3"
            />
            <BaseAutocompleteCustomField
              v-else
              v-model="workingTemplate.links[column].value"
              key-only
              class="shadow-3"
            />
            <q-input
              v-if="workingTemplate.links[column].value?.includes('.extra')"
              :label="$t('extra_attribute')"
              :model-value="workingTemplate.links[column].value.split('.').slice(2).join('.')"
              filled
              class="shadow-3 q-mt-sm"
              @update:model-value="(attributeName) => updateExtraAttribute(column, attributeName)"
            />
          </fieldset>

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
import { BLANK_PDF } from '@pdfme/common';
import { Designer } from '@pdfme/ui';
import { cloneDeep } from 'lodash';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseAutocompleteCustomField from '@/components/BaseAutocompleteCustomField.vue';
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

// Load custom fields on mount
const store = useStore();

watch(
  () => props.show,
  (show) => {
    if (show) {
      store.dispatch('getCustomFields');
      initTemplate();
      setTimeout(initDesigner, 500);
    }
  },
);

const templateDataOptions = [
  'current_date',
  'current_time',
  'current_user',

  'job.key',
  'job.qt_planned',
  'job.qt_completed',
  'job.phase_alias',
  'job.start_date',
  'job.start_time',
  'job.end_date',
  'job.end_time',
  'job.notes',
  'job.extra',

  'project.code',

  'work_order.code',
  'work_order.qt_planned',
  'work_order.qt_completed',
  'work_order.start_date',
  'work_order.start_time',
  'work_order.end_date',
  'work_order.end_time',
  'work_order.notes',
  'work_order.extra',

  'product.code',
  'product.description',

  'issue.id',
  'issue.open_date',
  'issue.open_time',
  'issue.open_user',
  'issue.close_date',
  'issue.close_time',
  'issue.close_user',
  'issue.status',

  'serial.code',
  'serial.qt',
  'serial.create_date',
  'serial.create_time',
  'serial.release_date',
  'serial.release_time',
  'serial.extra'
];

const { t, locale } = useI18n();
const emptyTemplate = computed(() => ({
  name: t('print_template_new'),
  description: undefined,
  links: {},
  template: {
    basePdf: BLANK_PDF,
    schemas: [],
  },
}));

const linkTypeOptions = computed(() => [
  {
    label: t('print_template_link_type.preset'),
    value: 'preset',
  },
  {
    label: t('print_template_link_type.custom_field'),
    value: 'custom_field',
  },
]);

const mode = ref();
const workingTemplate = ref();

/** @type {Designer} */
let designer;
function initDesigner() {
  const container = document.getElementById('pdf-designer');
  // Create a clean, cloneable version of the template
  const cleanTemplate = {
    basePdf: workingTemplate.value.template.basePdf,
    schemas: JSON.parse(JSON.stringify(workingTemplate.value.template.schemas || [])),
    columns: workingTemplate.value.template.columns ? [...workingTemplate.value.template.columns] : []
  };

  designer = new Designer({
    domContainer: container,
    template: cleanTemplate,
    options: { lang: locale.value },
  });
  designer.onChangeTemplate((template) => {
    let original_col = workingTemplate.value.links;
    workingTemplate.value.template = cloneDeep(template);
    workingTemplate.value.links = {};

    for (const column of template.columns ?? []) {
      if (original_col[column]) {
        workingTemplate.value.links[column] = original_col[column];
      } else {
        workingTemplate.value.links[column] = {
          type: 'preset',
          value: null,
        };
      }
    }
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
    // Destroy the existing designer before creating a new one
    if (designer) {
      designer.destroy();
    }
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

function updateExtraAttribute(column, attributeName) {
  const baseValue = workingTemplate.value.links[column].value.split('.').slice(0,2).join('.');
  if (['', null, undefined].includes(attributeName)) {
    workingTemplate.value.links[column].value = baseValue;
  } else {
    workingTemplate.value.links[column].value = `${baseValue}.${attributeName}`;
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
