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
      <div class="column full-height" style="min-height: 0">
      <!-- Toolbar: name, description, upload PDF, save -->
      <div
        v-if="workingTemplate"
        class="row q-pa-md q-col-gutter-md items-center surface1"
        style="border-bottom: 1px solid rgba(0,0,0,0.12)"
      >
        <div class="col-12 col-md-4">
          <q-input
            v-model="workingTemplate.name"
            filled
            dense
            :label="$t('name')"
            stack-label
            class="shadow-3"
          />
        </div>
        <div class="col">
          <q-input
            v-model="workingTemplate.description"
            autogrow
            filled
            dense
            :label="$t('description')"
            stack-label
            class="shadow-3"
          />
        </div>
        <div class="col-auto">
          <q-btn
            :label="$t('print_template_load_pdf')"
            color="primary"
            icon="mdi-upload"
            outline
            padding="sm"
            size="sm"
            @click="$refs.pdfFileInput.click()"
          />
        </div>

        <div class="col-auto">
          <q-btn
            :label="$t('save')"
            color="primary"
            icon="mdi-database-check"
            outline
            size="sm"
            padding="sm"
            @click="saveTemplate"
          />
        </div>
      </div>

      <!-- Designer container with custom left sidebar overlay -->
      <div class="pdf-designer-wrapper">
        <!-- Custom left sidebar for adding fields (absolutely positioned) -->
        <div v-if="workingTemplate" class="custom-left-sidebar column surface1 q-px-md">
          <q-btn
            flat
            dense
            square
            icon="mdi-format-text"
            class="q-mb-xs"
            @click="addField('text')"
          >
            <q-tooltip anchor="center right" self="center left" :offset="[10, 0]">
              {{ $t('field_type_text') }}
            </q-tooltip>
          </q-btn>
          <q-btn
            flat
            dense
            square
            icon="mdi-image"
            class="q-mb-sm"
            @click="addField('image')"
          >
            <q-tooltip anchor="center right" self="center left" :offset="[10, 0]">
              {{ $t('image') }}
            </q-tooltip>
          </q-btn>

          <q-btn
            v-for="bc in barcodeTypes"
            :key="bc.type"
            flat
            dense
            square
            :icon="bc.icon"
            class="q-mb-xs"
            @click="addField(bc.type)"
          >
            <q-tooltip anchor="center right" self="center left" :offset="[10, 0]">
              {{ bc.label }}
            </q-tooltip>
          </q-btn>
        </div>

        <div id="pdf-designer" class="pdf-designer-container" />
      </div>
      </div>

      <input
        ref="pdfFileInput"
        type="file"
        accept="application/pdf"
        style="opacity: 0; position: absolute; pointer-events: none"
        @change="uploadPdf($event.target.files[0])"
      />

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
import { Dark } from 'quasar';
import { api } from '@/boot/axios';
import { buildPlugins } from '@/lib/print/plugins';
import { encodeExpression, decodeExpression } from '@/lib/print/templateResolver.js';
import BaseActionCard from '@/components/BaseActionCard.vue';
import BaseDialog from '@/components/BaseDialog.vue';
import BaseModalScreen from '@/components/BaseModalScreen.vue';

const barcodeTypes = [
  { type: 'qrcode', label: 'QR Code', icon: 'mdi-qrcode' },
  { type: 'gs1datamatrix', label: 'DataMatrix', icon: 'mdi-data-matrix' },
  { type: 'ean13', label: 'EAN-13', icon: 'mdi-barcode' },
  { type: 'code39', label: 'Code 39', icon: 'mdi-barcode' },
  { type: 'code128', label: 'Code 128', icon: 'mdi-barcode' },
  { type: 'japanpost', label: 'Japan Post', icon: 'mdi-barcode' },
  { type: 'nw7', label: 'NW-7', icon: 'mdi-barcode' },
  { type: 'itf14', label: 'ITF-14', icon: 'mdi-barcode' },
  { type: 'upca', label: 'UPC-A', icon: 'mdi-barcode' },
  { type: 'upce', label: 'UPC-E', icon: 'mdi-barcode' },
];

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

const store = useStore();
const customFields = computed(() => store.state.form?.customFields ?? []);

watch(
  () => props.show,
  async (show) => {
    if (show) {
      await store.dispatch('getCustomFields');
      initTemplate();
      setTimeout(initDesigner, 500);
    }
  },
);

/** Convert v2/v4 schema (keyed object per page) to v5 format (array of objects with name property). */
function schemasToV5(schemas) {
  if (!schemas || !Array.isArray(schemas)) return [];
  return schemas.map((pageSchema) => {
    if (Array.isArray(pageSchema)) {
      return pageSchema;
    }
    return Object.entries(pageSchema).map(([fieldName, fieldSpec]) => ({
      ...fieldSpec,
      name: fieldName,
    }));
  });
}

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

const mode = ref();
const workingTemplate = ref();

/** Ant Design theme tokens mapped from app theme for pdfme Designer. */
const pdfmeTheme = computed(() => {
  const themeColors = store.getters.theme;
  const isDark = Dark.isActive;
  const textHigh = isDark ? 'rgba(255,255,255,0.87)' : 'rgba(30,52,58,1)';
  const textSecondary = isDark ? 'rgba(255,255,255,0.6)' : 'rgba(0,0,0,0.6)';
  const textTertiary = isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.45)';
  const textQuaternary = isDark ? 'rgba(255,255,255,0.25)' : 'rgba(0,0,0,0.25)';
  const inputBg = themeColors.surface2 || (isDark ? '#1F2A2D' : '#ffffff');
  return {
    token: {
      colorPrimary: themeColors.blue || '#22AED1',
      colorBgContainer: inputBg,
      colorBgElevated: themeColors.surface2 || (isDark ? '#242E31' : '#ffffff'),
      colorBgLayout: themeColors.surface1 || (isDark ? '#131E21' : '#eeeeee'),
      colorText: textHigh,
      colorTextSecondary: textSecondary,
      colorTextTertiary: textTertiary,
      colorTextQuaternary: textQuaternary,
      colorBorder: themeColors.grey || '#707070',
      colorSuccess: themeColors.green || '#0DAB76',
      colorError: themeColors.red || '#E71D36',
      colorWarning: themeColors.orange || '#FF9F1C',
    },
    components: {
      Input: {
        colorText: textHigh,
        colorTextPlaceholder: textQuaternary,
        colorBgContainer: inputBg,
        colorBorder: themeColors.grey || '#707070',
      },
      Select: {
        colorText: textHigh,
        colorTextPlaceholder: textQuaternary,
        colorBgContainer: inputBg,
        colorBgElevated: themeColors.surface2 || (isDark ? '#242E31' : '#ffffff'),
        colorBorder: themeColors.grey || '#707070',
        optionSelectedBg: themeColors.blue || '#22AED1',
      },
      InputNumber: {
        colorText: textHigh,
        colorTextPlaceholder: textQuaternary,
        colorBgContainer: inputBg,
        colorBorder: themeColors.grey || '#707070',
      },
    },
  };
});

/** @type {import('@pdfme/ui').Designer} */
let designer;

function getPlugins() {
  return buildPlugins(customFields.value);
}

function initDesigner() {
  const container = document.getElementById('pdf-designer');
  if (!container) return;

  const rawTemplate = workingTemplate.value.template;
  const schemasV5 = schemasToV5(rawTemplate.schemas);
  const cleanTemplate = JSON.parse(JSON.stringify({
    basePdf: rawTemplate.basePdf,
    schemas: schemasV5.length > 0 ? schemasV5 : [[]],
  }));

  const plugins = getPlugins();

  designer = new Designer({
    domContainer: container,
    template: cleanTemplate,
    options: {
      lang: locale.value,
      theme: pdfmeTheme.value,
    },
    plugins,
  });

  designer.onChangeTemplate((template) => {
    workingTemplate.value.template = cloneDeep(template);
  });
}

watch(pdfmeTheme, (newTheme) => {
  if (designer) {
    designer.updateOptions({ theme: newTheme });
  }
});

function addField(type) {
  if (!designer) return;
  const template = designer.getTemplate();
  const schemas = template.schemas && template.schemas.length > 0 ? [...template.schemas] : [[]];
  const pageIndex = 0;
  const pageSchemas = Array.isArray(schemas[pageIndex]) ? [...schemas[pageIndex]] : [];
  const plugins = getPlugins();
  const plugin = plugins[type];
  if (!plugin?.propPanel?.defaultSchema) return;

  const defaultSchema = cloneDeep(plugin.propPanel.defaultSchema);
  const baseName = type === 'text' ? 'text' : type === 'image' ? 'image' : type;
  const uniqueName = `${baseName}_${Date.now()}`;
  defaultSchema.name = uniqueName;
  defaultSchema.position = defaultSchema.position || { x: 20, y: 20 };
  defaultSchema.position = {
    x: defaultSchema.position.x,
    y: defaultSchema.position.y + pageSchemas.length * 12,
  };
  if (defaultSchema.width == null) defaultSchema.width = type === 'image' ? 60 : 80;
  if (defaultSchema.height == null) defaultSchema.height = type === 'image' ? 40 : 10;

  pageSchemas.push(defaultSchema);
  schemas[pageIndex] = pageSchemas;
  designer.updateTemplate({ ...template, schemas });
}

function closeDesigner() {
  if (designer) {
    designer.destroy();
    designer = null;
  }
  workingTemplate.value = undefined;
  emit('close');
}

async function uploadPdf(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = () => {
    workingTemplate.value.template.basePdf = reader.result;
    if (designer) {
      designer.destroy();
      designer = null;
    }
    initDesigner();
  };
}

/** Migrate old customFieldKey to linkValue for backward compatibility */
function migrateTemplateSchema(template) {
  if (!template?.template?.schemas) return template;

  const schemas = template.template.schemas;
  schemas.forEach((pageSchema) => {
    const fields = Array.isArray(pageSchema) ? pageSchema : Object.values(pageSchema);
    fields.forEach((field) => {
      // Migrate old customFieldKey to new unified linkValue field
      if (field.customFieldKey && !field.linkValue) {
        field.linkValue = field.customFieldKey;
        delete field.customFieldKey;
      }
    });
  });

  return template;
}

/**
 * Decode all template_expression fields in-place so the canvas shows the human-readable form.
 * Sets field.content = decodeExpression(field.templateExpression, customFields)
 */
function decodeTemplateExpressions(template, fields) {
  if (!template?.template?.schemas) return;
  template.template.schemas.forEach((pageSchema) => {
    const schemaFields = Array.isArray(pageSchema) ? pageSchema : Object.values(pageSchema);
    schemaFields.forEach((field) => {
      if (field.linkType === 'template_expression') {
        field.content = decodeExpression(field.templateExpression, fields);
      }
    });
  });
}

/**
 * Encode all template_expression fields in a deep-cloned template for storage.
 * Never mutates the original — returns the encoded copy.
 */
function encodeTemplateExpressions(template, fields) {
  const cloned = cloneDeep(template);
  if (!cloned?.schemas) return cloned;
  cloned.schemas.forEach((pageSchema) => {
    const schemaFields = Array.isArray(pageSchema) ? pageSchema : Object.values(pageSchema);
    schemaFields.forEach((field) => {
      if (field.linkType === 'template_expression') {
        field.templateExpression = encodeExpression(field.templateExpression, fields);
      }
    });
  });
  return cloned;
}

function initTemplate() {
  if (props.editTemplate) {
    mode.value = 'edit';
    const cloned = migrateTemplateSchema(cloneDeep(props.editTemplate));
    decodeTemplateExpressions(cloned, customFields.value);
    workingTemplate.value = cloned;
  } else {
    mode.value = 'new';
    workingTemplate.value = cloneDeep(emptyTemplate.value);
  }
}

async function saveTemplate() {
  const templateFromDesigner = designer.getTemplate();
  const encodedTemplate = encodeTemplateExpressions(cloneDeep(templateFromDesigner), customFields.value);
  await api.request({
    method: mode.value === 'new' ? 'POST' : 'PUT',
    url: 'print-template',
    data: {
      ...workingTemplate.value,
      template: encodedTemplate,
    },
  });
  emit('saved');
  closeDesigner();
}

const showRename = ref(false);
function cancelRename() {
  showRename.value = false;
}
</script>

<style scoped>
.pdf-designer-wrapper {
  flex: 1;
  min-height: 0;
  position: relative;
}

.custom-left-sidebar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  overflow-y: auto;
}

.pdf-designer-container {
  width: 100%;
  height: 100%;
  position: relative;
}

/* Hide pdfme left sidebar (45px icon bar) so our custom sidebar replaces it */
.pdf-designer-container :deep([class*="LeftSidebar"]),
.pdf-designer-container :deep([class*="left-sidebar"]),
.pdf-designer-container :deep(> div > div:first-child[style*="width: 45px"]),
.pdf-designer-container :deep(> div > div:first-child[style*="width:45px"]) {
  display: none !important;
}
</style>

<style>
/* Ant Design Select/Cascader dropdowns are portalled to document.body with z-index ~1050.
   Quasar q-dialog uses z-index ~6000. Override so pdfme prop-panel dropdowns are visible. */
.ant-select-dropdown,
.ant-cascader-dropdown {
  z-index: 9999 !important;
}
</style>
