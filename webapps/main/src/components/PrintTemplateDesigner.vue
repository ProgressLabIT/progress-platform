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
        <div class="col-12 col-md-auto">
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
            :label="$t('print_template_page_size')"
            color="primary"
            icon="mdi-resize"
            outline
            padding="sm"
            size="sm"
            @click="openPageSizeDialog"
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

        <div class="col-auto">
          <q-btn
            flat
            round
            dense
            icon="mdi-help-circle-outline"
            @click="showHelp = true"
          >
            <q-tooltip>{{ $t('print_template_help.title') }}</q-tooltip>
          </q-btn>
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
            class="q-mb-xs"
            @click="addField('image')"
          >
            <q-tooltip anchor="center right" self="center left" :offset="[10, 0]">
              {{ $t('image') }}
            </q-tooltip>
          </q-btn>
          <q-btn
            flat
            dense
            square
            icon="mdi-text-box-outline"
            class="q-mb-sm"
            @click="addTemplateExpressionField()"
          >
            <q-tooltip anchor="center right" self="center left" :offset="[10, 0]">
              {{ $t('field_type_template_string') }}
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

      <BaseDialog :show="showPageSize" :no-backdrop-dismiss="false" @close="showPageSize = false">
        <q-card class="surface2" style="width: 360px; max-width: 95vw">
          <q-card-section>
            <div class="text-h6 display highlight">{{ $t('print_template_page_size') }}</div>
          </q-card-section>

          <q-card-section class="q-pt-none q-col-gutter-sm column">
            <q-select
              v-model="pageSizePreset"
              :options="PAGE_SIZE_PRESETS"
              option-label="label"
              filled
              dense
              :label="$t('print_template_page_preset')"
              @update:model-value="onPresetSelected"
            />
            <div class="row q-col-gutter-sm">
              <div class="col">
                <q-input
                  v-model.number="pageSizeWidth"
                  type="number"
                  filled
                  dense
                  :label="$t('width_mm')"
                  suffix="mm"
                />
              </div>
              <div class="col">
                <q-input
                  v-model.number="pageSizeHeight"
                  type="number"
                  filled
                  dense
                  :label="$t('height_mm')"
                  suffix="mm"
                />
              </div>
            </div>
          </q-card-section>

          <q-card-actions align="right">
            <q-btn flat :label="$t('cancel')" @click="showPageSize = false" />
            <q-btn flat color="primary" :label="$t('confirm')" @click="confirmPageSize" />
          </q-card-actions>
        </q-card>
      </BaseDialog>

      <BaseDialog :show="showHelp" :no-backdrop-dismiss="false" @close="showHelp = false">
        <q-card class="surface2" style="width: 660px; max-width: 95vw; max-height: 90vh; display: flex; flex-direction: column;">
          <q-card-section class="row items-center q-pb-none">
            <div class="text-h6 display highlight">{{ $t('print_template_help.title') }}</div>
            <q-space />
            <q-btn flat round dense icon="mdi-close" @click="showHelp = false" />
          </q-card-section>

          <q-card-section class="scroll col q-pt-sm" style="min-height: 0;">
            <p class="text-body2">{{ $t('print_template_help.overview') }}</p>

            <div class="text-subtitle2 highlight text-weight-medium q-mt-md q-mb-xs">
              {{ $t('print_template_help.field_types_title') }}
            </div>
            <q-list dense>
              <q-item v-for="ft in fieldTypeHelp" :key="ft.key" class="q-px-none">
                <q-item-section avatar>
                  <q-icon :name="ft.icon" size="sm" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-medium">{{ ft.label }}</q-item-label>
                  <q-item-label caption>{{ ft.desc }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-subtitle2 highlight text-weight-medium q-mt-md q-mb-xs">
              {{ $t('print_template_help.link_types_title') }}
            </div>
            <q-list dense>
              <q-item v-for="lt in linkTypeHelp" :key="lt.key" class="q-px-none">
                <q-item-section>
                  <q-item-label><code class="text-caption">{{ lt.key }}</code></q-item-label>
                  <q-item-label caption>{{ lt.desc }}</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>

            <div class="text-subtitle2 highlight text-weight-medium q-mt-md q-mb-xs">
              {{ $t('print_template_help.token_syntax_title') }}
            </div>
            <p class="text-body2 q-mb-xs">{{ $t('print_template_help.token_syntax') }}</p>
            <div class="text-body2 q-mb-xs q-pl-sm">
              <div><code>{{ tokenExamples.field }}</code> — {{ $t('print_template_help.token_field') }}</div>
              <div><code>{{ tokenExamples.preset }}</code> — {{ $t('print_template_help.token_preset') }}</div>
              <div><code>{{ tokenExamples.cf }}</code> — {{ $t('print_template_help.token_cf') }}</div>
            </div>
            <p class="text-body2 q-mt-sm">{{ $t('print_template_help.operators') }}</p>

            <div class="text-subtitle2 highlight text-weight-medium q-mt-md q-mb-xs">
              {{ $t('print_template_help.computed_title') }}
            </div>
            <p class="text-body2 q-mb-sm">{{ $t('print_template_help.computed_intro') }}</p>
            <q-markup-table flat dense bordered wrap-cells class="text-body2">
              <thead>
                <tr>
                  <th class="text-left" style="width: 45%">{{ $t('print_template_help.col_function') }}</th>
                  <th class="text-left">{{ $t('print_template_help.col_description') }}</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="group in helpFunctionGroups" :key="group.title">
                  <tr>
                    <td
                      colspan="2"
                      class="text-caption text-weight-bold q-py-xs"
                      style="background: rgba(128,128,128,0.08)"
                    >
                      {{ group.title }}
                    </td>
                  </tr>
                  <tr v-for="fn in group.fns" :key="fn.fn">
                    <td><code>{{ fn.fn }}</code></td>
                    <td>{{ fn.desc }}</td>
                  </tr>
                </template>
              </tbody>
            </q-markup-table>
          </q-card-section>

          <q-card-actions align="right" class="q-pt-none">
            <q-btn flat :label="$capitalize($t('close'))" @click="showHelp = false" />
          </q-card-actions>
        </q-card>
      </BaseDialog>
    </template>
  </BaseModalScreen>
</template>

<script setup>
import { BLANK_A4_PDF } from '@pdfme/common';
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
  { type: 'datamatrix', label: 'DataMatrix', icon: 'mdi-data-matrix' },
  { type: 'gs1datamatrix', label: 'GS1 DataMatrix', icon: 'mdi-data-matrix' },
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
const PAGE_SIZE_PRESETS = [
  { label: 'A4 Portrait',   width: 210,   height: 297,  padding: [10, 10, 10, 10] },
  { label: 'A4 Landscape',  width: 297,   height: 210,  padding: [10, 10, 10, 10] },
  { label: 'A5 Portrait',   width: 148,   height: 210,  padding: [10, 10, 10, 10] },
  { label: 'A3 Portrait',   width: 297,   height: 420,  padding: [10, 10, 10, 10] },
  { label: 'Letter',        width: 215.9, height: 279.4, padding: [10, 10, 10, 10] },
  { label: 'Label 100×50',  width: 100,   height: 50,   padding: [2, 2, 2, 2] },
  { label: 'Label 100×70',  width: 100,   height: 70,   padding: [2, 2, 2, 2] },
];

const emptyTemplate = computed(() => ({
  name: t('print_template_new'),
  description: undefined,
  links: {},
  template: {
    basePdf: { ...BLANK_A4_PDF },
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

// Guards against re-entrancy: our restore logic clicks .pdfme-ui-page-next which itself
// fires onPageChange. Without this flag the onPageChange handler would re-invoke the
// restore loop for every intermediate click.
let isRestoringPageCursor = false;

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
    // Preserve blank PDF basePdf: the designer keeps its initial basePdf internally
    // and does not update it via updateTemplate, so we must not let it overwrite
    // the dimensions the user has set in the toolbar.
    const trackedBasePdf = workingTemplate.value.template?.basePdf;
    workingTemplate.value.template = cloneDeep(template);
    if (trackedBasePdf != null && typeof trackedBasePdf === 'object') {
      workingTemplate.value.template.basePdf = trackedBasePdf;
    }
  });

  // When the user uses pdfme's built-in "Add page after" menu (or any other internal
  // navigation), pdfme's internal q() sets the cursor then awaits W() which resets it
  // back to 0. After q() completes it fires onPageChange with the target page. If the
  // UI ended up on page 0 instead (compact template, no scroll-driven resync), drive
  // the same DOM-level restore we use for addField.
  designer.onPageChange((info) => {
    if (isRestoringPageCursor) return;
    if (!info || info.currentPage <= 0) return;
    requestAnimationFrame(() => {
      const c = document.getElementById('pdf-designer');
      const prevBtn = c?.querySelector('.pdfme-ui-page-prev');
      if (prevBtn && prevBtn.disabled) {
        isRestoringPageCursor = true;
        restorePageCursorAfterReset(info.currentPage, () => { isRestoringPageCursor = false; });
      }
    });
  });
}

watch(pdfmeTheme, (newTheme) => {
  if (designer) {
    designer.updateOptions({ theme: newTheme });
  }
});

function addField(type, overrides = {}) {
  if (!designer) return;
  const template = designer.getTemplate();
  const pageIndex = typeof designer.getPageCursor === 'function' ? designer.getPageCursor() : 0;
  const schemas = template.schemas && template.schemas.length > 0 ? [...template.schemas] : [[]];
  while (schemas.length <= pageIndex) schemas.push([]);
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

  Object.assign(defaultSchema, overrides);

  pageSchemas.push(defaultSchema);
  schemas[pageIndex] = pageSchemas;

  designer.updateTemplate({ ...template, schemas });

  if (pageIndex > 0) {
    isRestoringPageCursor = true;
    restorePageCursorAfterReset(pageIndex, () => { isRestoringPageCursor = false; });
  }
}

/**
 * pdfme's updateTemplate triggers an async internal callback that resets its React-state
 * pageCursor to 0 and smooth-scrolls the canvas to top. When the template is compact enough
 * that all pages fit in the viewport, no scroll happens and pdfme's internal useScrollPageCursor
 * cannot resync — so the wrong page is shown as active.
 *
 * There is no public Designer API to set pageCursor. The only navigation hook is the
 * .pdfme-ui-page-next button in the CtlBar, whose onClick calls the internal setPageCursor.
 * page-prev's `disabled` attribute is a reliable signal: it flips false→true exactly when
 * pdfme finishes resetting to cursor=0. We observe that transition and then click page-next
 * once per animation frame (each click triggers a React render so the next click reads the
 * updated cursor from its closure).
 */
function restorePageCursorAfterReset(targetPage, onDone) {
  const finish = () => { onDone && onDone(); };
  const container = document.getElementById('pdf-designer');
  if (!container) { finish(); return; }
  const prevBtn = container.querySelector('.pdfme-ui-page-prev');
  if (!prevBtn) { finish(); return; }

  let clicksLeft = targetPage;
  const advance = () => {
    if (clicksLeft <= 0) { finish(); return; }
    const nextBtn = container.querySelector('.pdfme-ui-page-next');
    if (!nextBtn || nextBtn.disabled) { finish(); return; }
    nextBtn.click();
    clicksLeft -= 1;
    if (clicksLeft > 0) requestAnimationFrame(advance);
    else finish();
  };

  if (prevBtn.disabled) {
    advance();
    return;
  }
  const observer = new MutationObserver(() => {
    if (prevBtn.disabled) {
      observer.disconnect();
      advance();
    }
  });
  observer.observe(prevBtn, { attributes: true, attributeFilter: ['disabled'] });
}

function addTemplateExpressionField() {
  addField('text', { linkType: 'template_expression', templateExpression: '' });
}

function closeDesigner() {
  if (designer) {
    designer.destroy();
    designer = null;
  }
  workingTemplate.value = undefined;
  emit('close');
}

const showPageSize = ref(false);
const pageSizePreset = ref(null);
const pageSizeWidth = ref(210);
const pageSizeHeight = ref(297);
const pageSizePadding = ref([10, 10, 10, 10]);

function openPageSizeDialog() {
  const bp = workingTemplate.value?.template?.basePdf;
  if (bp != null && typeof bp === 'object') {
    pageSizeWidth.value = bp.width;
    pageSizeHeight.value = bp.height;
    pageSizePadding.value = bp.padding ?? [10, 10, 10, 10];
  } else {
    pageSizeWidth.value = 210;
    pageSizeHeight.value = 297;
    pageSizePadding.value = [10, 10, 10, 10];
  }
  pageSizePreset.value = PAGE_SIZE_PRESETS.find(
    (p) => p.width === pageSizeWidth.value && p.height === pageSizeHeight.value,
  ) ?? null;
  showPageSize.value = true;
}

function onPresetSelected(preset) {
  if (!preset) return;
  pageSizeWidth.value = preset.width;
  pageSizeHeight.value = preset.height;
  pageSizePadding.value = preset.padding;
}

function confirmPageSize() {
  if (!workingTemplate.value) return;
  workingTemplate.value.template.basePdf = {
    width: pageSizeWidth.value,
    height: pageSizeHeight.value,
    padding: pageSizePadding.value,
  };
  showPageSize.value = false;
  if (designer) {
    designer.destroy();
    designer = null;
  }
  initDesigner();
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
 * Decode all template_expression fields in-place so the canvas and Expression input show the human-readable form.
 * - Text fields: content = decoded expression (readable canvas preview)
 * - Barcode/other fields: content = plugin defaultSchema.content (valid sample so designer renders correctly)
 */
function decodeTemplateExpressions(template, fields) {
  if (!template?.template?.schemas) return;
  const plugins = getPlugins();
  template.template.schemas.forEach((pageSchema) => {
    const schemaFields = Array.isArray(pageSchema) ? pageSchema : Object.values(pageSchema);
    schemaFields.forEach((field) => {
      if (field.linkType === 'template_expression') {
        field.templateExpression = decodeExpression(field.templateExpression, fields);
        if (field.type === 'text') {
          field.content = field.templateExpression;
        } else {
          // Restore default sample content so the barcode renders in the designer
          const defaultContent = plugins[field.type]?.propPanel?.defaultSchema?.content;
          if (defaultContent) field.content = defaultContent;
        }
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
  const templateToSave = cloneDeep(templateFromDesigner);
  // Use the tracked basePdf from workingTemplate: the designer keeps its initial basePdf
  // internally and does not reflect live dimension changes from the toolbar inputs.
  templateToSave.basePdf = workingTemplate.value.template?.basePdf ?? templateFromDesigner.basePdf;
  const encodedTemplate = encodeTemplateExpressions(templateToSave, customFields.value);
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

const showHelp = ref(false);

/** Token examples for the help dialog — kept as data so Vue does not parse the braces. */
const tokenExamples = {
  field: '{{field::FieldName}}',
  preset: '{{preset.key}}',
  cf: '{{cf::slug}}',
};

const fieldTypeHelp = computed(() => [
  { key: 'text', icon: 'mdi-format-text', label: t('field_type_text'), desc: t('print_template_help.field_type_text') },
  { key: 'image', icon: 'mdi-image', label: t('image'), desc: t('print_template_help.field_type_image') },
  { key: 'template_string', icon: 'mdi-text-box-outline', label: t('field_type_template_string'), desc: t('print_template_help.field_type_template_string') },
  { key: 'barcode', icon: 'mdi-barcode', label: t('print_template_barcodes'), desc: t('print_template_help.field_type_barcode') },
]);

const linkTypeHelp = computed(() => [
  { key: 'none', desc: t('print_template_help.link_none') },
  { key: 'preset', desc: t('print_template_help.link_preset') },
  { key: 'custom_field', desc: t('print_template_help.link_custom_field') },
  { key: 'template_expression', desc: t('print_template_help.link_template_expression') },
  { key: 'computed', desc: t('print_template_help.link_computed') },
]);

const helpFunctionGroups = computed(() => [
  {
    title: t('print_template_help.category_string'),
    fns: [
      { fn: 'CONCAT(a, b, ...)', desc: t('print_template_help.fn_concat') },
      { fn: 'UPPER(s)', desc: t('print_template_help.fn_upper') },
      { fn: 'LOWER(s)', desc: t('print_template_help.fn_lower') },
      { fn: 'SPLIT(str, delim, index)', desc: t('print_template_help.fn_split') },
    ],
  },
  {
    title: t('print_template_help.category_math'),
    fns: [
      { fn: 'ROUND(n, decimals?)', desc: t('print_template_help.fn_round') },
      { fn: 'ABS(n)', desc: t('print_template_help.fn_abs') },
      { fn: 'CEIL(n)', desc: t('print_template_help.fn_ceil') },
      { fn: 'FLOOR(n)', desc: t('print_template_help.fn_floor') },
    ],
  },
  {
    title: t('print_template_help.category_date'),
    fns: [
      { fn: 'NOW()', desc: t('print_template_help.fn_now') },
      { fn: 'DATE(fmt, ...)', desc: t('print_template_help.fn_date') },
      { fn: 'FORMAT_DATE(d, pattern)', desc: t('print_template_help.fn_format_date') },
      { fn: 'DATE_ADD(d, amount, unit)', desc: t('print_template_help.fn_date_add') },
      { fn: 'DAYS_BETWEEN(d1, d2)', desc: t('print_template_help.fn_days_between') },
      { fn: 'YEAR(d) / MONTH(d) / DAY(d)', desc: t('print_template_help.fn_ymd') },
      { fn: 'WEEK(d)', desc: t('print_template_help.fn_week') },
    ],
  },
  {
    title: t('print_template_help.category_conditional'),
    fns: [
      { fn: 'IF(cond, then, else)', desc: t('print_template_help.fn_if') },
    ],
  },
]);
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
/* Ant Design dropdowns are portalled to document.body with z-index ~1050.
   Quasar q-dialog uses z-index ~6000. Override so pdfme prop-panel and ctl-bar menus are visible. */
.ant-select-dropdown,
.ant-cascader-dropdown,
.ant-dropdown {
  z-index: 9999 !important;
}
</style>
