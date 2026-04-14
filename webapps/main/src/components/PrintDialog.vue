<template>
  <!-- TODO: Create a better base component for using with custom dialog plugin components -->
  <BaseDialog
    :show="true"
    :get-dialog-ref="getDialogRef"
    :no-backdrop-dismiss="activeStep > 0"
    @close="onDialogHide"
  >
    <q-stepper
      v-model="activeStep"
      header-nav
      class="surface1"
      :style="{ minWidth: `${dialogWidth}px` }"
    >
      <q-step
        v-if="allowSelectTemplate"
        :name="0"
        :done="activeStep > 0"
        active-icon="mdi-file-document"
        :title="$t('printDialog.chooseTemplate.title')"
      >
        <q-card-section v-if="templates.length === 0" class="text-center">
          <q-icon size="xl" color="low" name="mdi-alert-circle-outline" />
          <div class="text-h3 q-mt-sm">
            {{ $t('printDialog.chooseTemplate.noTemplates') }}
          </div>
        </q-card-section>
        <q-card-section v-else class="column scroll q-gutter-md">
          <PrintTemplateCard
            v-for="template in templates"
            :key="template._key"
            :template="template"
          >
            <template #extra-actions>
              <q-space />

              <q-btn
                dense
                size="md"
                icon="mdi-check-circle"
                :label="$t('select')"
                color="primary"
                @click="selectTemplate(template)"
              />
            </template>
          </PrintTemplateCard>
        </q-card-section>

        <q-stepper-navigation class="flex items-center">
          <q-btn
            :label="$t('cancel')"
            color="theme-grey"
            @click="onDialogCancel"
          />

          <q-space />

          <span>
            {{ $t('printDialog.chooseTemplate.nextInstruction') }}
          </span>
        </q-stepper-navigation>
      </q-step>

      <q-step
        :name="1"
        :done="activeStep > 1"
        :disable="selectedTemplate === undefined && !isLoadingTemplate"
        icon="mdi-pencil"
        :title="$t('printDialog.fillData.title')"
      >
        <LoadingSignal v-if="isLoadingTemplate" />
        <template v-else>
          <!-- serialSource sets either wo_key for WorkOrderContext or batch_key for StepContext -->
          <BaseAutocompleteSerial
            v-if="hasSerialLink"
            :value="context.serial"
            v-bind="props.context.serialSource"
            :can_search="serialModelInitalValue.length <= 0"
            :label="$capitalize($t('serial'))"
            :include_unreleased="true"
            :disable="serialModelInitalValue.length === 1"
            :show-link-status="false"
            :show-inventory-status="false"
            @select="selectSerial"
          >
          </BaseAutocompleteSerial>
          <template
            v-for="(pageSchema, index) in selectedTemplate.template.schemas"
            :key="index"
          >
            <fieldset
              v-if="normalizePageSchema(pageSchema).length > 0"
              class="q-pa-md q-my-md column"
              style="gap: 16px"
            >
              <legend class="text-h5 q-px-sm">
                {{ $t('printDialog.fillData.page', { number: index + 1 }) }}
              </legend>

              <template
                v-for="(field, fIndex) in normalizePageSchema(pageSchema)"
                :key="`${index}-${fIndex}-${field.name || fIndex}`"
              >
                <!-- Skip read-only fields, but always show computed and template_expression fields -->
                <template v-if="!field.readOnly || field.linkType === 'computed' || field.linkType === 'template_expression'">
                  <template v-if="field.type === 'image'">
                    <div class="text-body2 text-weight-medium">
                      {{ printFieldDisplayLabel(field, fIndex) }}
                      <span v-if="field.required" class="text-theme-red"> * </span>
                    </div>
                    <q-img
                      :src="formModel[field.name]"
                      fit="contain"
                      style="width: 300px"
                    >
                      <template #error>
                        <div class="bg-grey-2 text-grey-6" style="word-break: break-word;">
                          <div class="text-center">
                            <q-icon name="mdi-image-off-outline" size="md" />
                            <div class="smaller q-mt-xs">{{ $t('image_not_available_at_path') }}</div>
                            <div class="smaller q-mt-xs">{{ formModel[field.name] }}</div>
                          </div>
                        </div>
                      </template>
                    </q-img>
                  </template>
                  <!-- External label: q-input #label + filled hides floating labels once filled / in some themes -->
                  <div v-else class="column q-gutter-xs">
                    <div class="row items-center no-wrap q-gutter-xs text-body2 text-weight-medium">
                      <q-icon
                        v-if="field.linkType === 'computed'"
                        name="mdi-function-variant"
                        size="xs"
                        class="flex-none"
                      />
                      <span>{{ printFieldDisplayLabel(field, fIndex) }}</span>
                      <span v-if="field.required" class="text-theme-red"> * </span>
                    </div>
                    <q-input
                      v-model="formModel[field.name]"
                      filled
                      dense
                      hide-bottom-space
                      :type="field.linkType === 'template_expression' && field.type !== 'text' ? 'textarea' : undefined"
                      :autogrow="field.linkType === 'template_expression' && field.type !== 'text'"
                      :readonly="field.linkType === 'computed' || (field.linkType === 'template_expression' && field.type !== 'text')"
                      @blur="recomputeFields"
                    />
                  </div>
                </template>
              </template>
            </fieldset>
          </template>
        </template>

        <q-stepper-navigation class="flex q-gutter-sm">
          <q-btn
            :label="$t('cancel')"
            color="theme-grey"
            @click="onDialogCancel"
          />

          <q-space />

          <q-btn v-if="!(activeStep === 1 && !allowSelectTemplate)" :label="$t('back')" color="theme-grey" @click="activeStep--" />
          <q-btn
            :label="$t('next')"
            color="primary"
            :disable="isLoadingTemplate"
            @click="goToPreview"
          />
        </q-stepper-navigation>
      </q-step>

      <q-step
        :name="2"
        :disable="selectedTemplate === undefined && !isLoadingTemplate"
        :header-nav="false"
        icon="mdi-printer-eye"
        active-icon="mdi-printer-eye"
        :title="$t('printDialog.preview.title')"
      >
        <div class="col scroll full-width flex flex-center">
          <vue-pdf-embed
            v-if="previewSrc"
            :source="previewSrc"
            :width="pdfWidth"
          />
        </div>

        <q-stepper-navigation class="flex q-gutter-sm">
          <template v-if="!isPrinting">
            <q-btn
              :label="$t('cancel')"
              color="theme-grey"
              @click="onDialogCancel"
            />

            <q-space />

            <q-btn :label="$t('back')" color="theme-grey" @click="activeStep--" />
            <q-btn
              :label="$t('save')"
              color="primary"
              :disable="isLoadingTemplate"
              @click="
                onDialogOK({
                  src: previewSrc,
                  printTemplate: selectedTemplate,
                  data: formModel,
                })
              "
            />
            <q-btn
              v-if="selectedPrinter"
              :label="$t('printDialog.sendToPrinter.label', { name: selectedPrinter.name })"
              color="primary"
              icon="mdi-printer"
              :disable="isLoadingTemplate"
              @click="showCopiesPrompt = true"
            />
          </template>
          <template v-else>
            <q-space />
            <q-spinner color="primary" size="2em" />
            <q-space />
          </template>
        </q-stepper-navigation>
      </q-step>
    </q-stepper>
    <BasePrompt
      :show="showCopiesPrompt"
      :prompt="$t('printDialog.sendToPrinter.copiesPrompt')"
      :help-text="$t('printDialog.sendToPrinter.copiesHelpText')"
      input_type="number"
      :initial_value="1"
      :min="1"
      :require-change="false"
      confirm-label="print"
      @close="showCopiesPrompt = false"
      @update="onCopiesConfirmed"
    />
  </BaseDialog>
</template>

<script setup>
import { generate } from '@pdfme/generator';
import { useDialogPluginComponent, Notify } from 'quasar';
import { nextTick, ref, reactive, toRaw, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import VuePdfEmbed from 'vue-pdf-embed';
import { api } from '@/boot/axios';
import { buildPlugins } from '@/lib/print/plugins';
import { resolveExpression } from '@/lib/print/templateResolver.js';
import { evaluateComputed, buildValuesMap } from '@/lib/print/computedResolver.js';
import { useConfigStore } from '@/stores/config';
import { generateZpl } from '@/lib/print/zpl.js';
import { processZplImageFields } from '@/lib/print/zplImage.js';
import { sendToPrintService } from '@/lib/print/index.js';
import BaseDialog from '@/components/BaseDialog.vue';
import BasePrompt from '@/components/BasePrompt.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import PrintTemplateCard from '@/components/PrintTemplateCard.vue';
import BaseAutocompleteSerial from './BaseAutocompleteSerial.vue';

const pdfmePlugins = buildPlugins([]);

/** Normalize page schema to array of { name, type, ... } (v5 format). Supports v2/v4 (keyed object) and v5 (array). */
function normalizePageSchema(pageSchema) {
  if (!pageSchema) return [];
  if (Array.isArray(pageSchema)) {
    return pageSchema.map((field) => ({
      ...field,
      name: field.name || field.key,
    }));
  }
  return Object.entries(pageSchema).map(([fieldName, fieldSpec]) => ({
    ...fieldSpec,
    name: fieldName,
  }));
}

/** Label shown above print form fields: custom field title when linked, else optional schema label, else template field name. */
function printFieldDisplayLabel(field, fieldIndex = null) {
  const templateName = String(field.name ?? field.key ?? field.id ?? '').trim();
  const schemaLabel = typeof field.label === 'string' ? field.label.trim() : '';
  if (field.linkType === 'custom_field') {
    const cfKey = field.linkValue || field.customFieldKey || '';
    const list = store.state.form.customFields || [];
    const cf = list.find((c) => c._key === cfKey);
    const fromCf = (cf?.name || cf?.default_label || '').trim();
    if (fromCf) return fromCf;
    const rest = schemaLabel || templateName;
    if (rest) return rest;
    return fieldIndex != null ? t('printDialog.fillData.unnamedField', { n: fieldIndex + 1 }) : '';
  }
  const rest = schemaLabel || templateName;
  if (rest) return rest;
  return fieldIndex != null ? t('printDialog.fillData.unnamedField', { n: fieldIndex + 1 }) : '';
}

/** Get field names and link config from template + record. Supports v2/v4 (columns + links) and v5 (linkType/linkValue on schema). */
function getFieldNamesAndLinks(data) {
  const template = data.template || {};
  const schemas = template.schemas || [];
  const columns = template.columns;
  const links = data.links || {};

  if (columns && Array.isArray(columns) && columns.length > 0) {
    return {
      fieldNames: columns,
      getLink: (fieldName) => links[fieldName] || null,
    };
  }

  const fieldNames = [];
  const linkByField = {};
  const contentByField = {};
  for (const pageSchema of schemas) {
    const fields = normalizePageSchema(pageSchema);
    for (const field of fields) {
      const name = field.name || field.key;
      if (name) {
        fieldNames.push(name);
        if (field.content) contentByField[name] = field.content;
        if (field.linkType && field.linkType !== 'none') {
          // Support both new linkValue field and old customFieldKey for backward compatibility
          let value = field.linkValue || field.customFieldKey || '';
          if (field.linkType === 'preset' && field.extraPath) {
            value = value ? `${value}.${field.extraPath}` : field.extraPath;
          }
          linkByField[name] = {
            type: field.linkType,
            value,
            // For template_expression fields, the expression lives on the schema field itself
            templateExpression: field.templateExpression || '',
          };
        }
      }
    }
  }
  return {
    fieldNames: [...new Set(fieldNames)],
    getLink: (fieldName) => linkByField[fieldName] || null,
    getContent: (fieldName) => contentByField[fieldName] || '',
  };
}

/** Normalize full schemas to v5 (array of arrays) for generate(). */
function schemasToV5(schemas) {
  if (!schemas || !Array.isArray(schemas)) return [];
  return schemas.map(normalizePageSchema);
}

/** Convert reactive/proxy basePdf into a plain clone for pdfme generate(). */
function normalizeBasePdf(basePdf) {
  if (basePdf != null && typeof basePdf === 'object') {
    return JSON.parse(JSON.stringify(toRaw(basePdf)));
  }
  return basePdf;
}

const props = defineProps({
  context: {
    type: Object,
    required: true,
  },
  templates: {
    type: Array,
    required: true,
  },
});

defineEmits(useDialogPluginComponent.emitsObject);

const { t } = useI18n();
const store = useStore();
const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } =
  useDialogPluginComponent();
// This can't be inside the template due to unwrapping
// See: https://github.com/vuejs/composition-api/issues/317#issuecomment-1069145915
const getDialogRef = () => dialogRef;

const { config } = useConfigStore();
const isPrinting = ref(false);
const showCopiesPrompt = ref(false);

const selectedPrinter = computed(() => {
  const prefValue = store.state.session.user?.preferences?.printer;
  if (!prefValue) return null;
  return config.printers.find(p => `${p.host}:${p.port}` === prefValue) ?? null;
});

const activeStep = ref(0);
const allowSelectTemplate = ref(true);

const selectedTemplate = ref();
const isLoadingTemplate = ref(false);
let formModel = undefined;
// const serialModel = ref();
const serialModelInitalValue = ref([]);

const selectedTemplateBK = ref();
const hasSerialLink = ref(false);
const previewSrc = ref();
let computedFieldDefs = [];
let computedFieldNames = new Set();
let templateExprFieldDefs = [];
let templateExprFieldNames = new Set();
let stopComputedWatcher = null;
let currentGetLink = null;

function recomputeFields() {
  if (computedFieldDefs.length === 0 && templateExprFieldDefs.length === 0) return;
  if (!formModel) return;
  const allCustomFields = store.state.form.customFields;

  if (computedFieldDefs.length > 0) {
    const valMap = buildValuesMap(formModel, props.context, allCustomFields);
    const MAX_PASSES = 5;
    for (let pass = 0; pass < MAX_PASSES; pass++) {
      let changed = false;
      for (const { name, expression } of computedFieldDefs) {
        const newVal = String(evaluateComputed(expression, valMap) ?? '');
        if (formModel[name] !== newVal) {
          formModel[name] = newVal;
          valMap.set(`field::${name}`, newVal);
          changed = true;
        }
      }
      if (!changed) break;
    }
  }

  for (const { name, expression } of templateExprFieldDefs) {
    const newVal = resolveExpression(expression, props.context, allCustomFields, formModel);
    if (formModel[name] !== newVal) {
      formModel[name] = newVal;
    }
  }
}

function resetState() {
  activeStep.value = 0;
  allowSelectTemplate.value = true;
  selectedTemplate.value = undefined;
  isLoadingTemplate.value = false;
  formModel = undefined;
  serialModelInitalValue.value = [];
  selectedTemplateBK.value = undefined;
  hasSerialLink.value = false;
  previewSrc.value = undefined;
  if (stopComputedWatcher) { stopComputedWatcher(); stopComputedWatcher = null; }
  computedFieldDefs = [];
  computedFieldNames = new Set();
  templateExprFieldDefs = [];
  templateExprFieldNames = new Set();
  currentGetLink = null;
}

function initialize() {
  resetState();
  if (props.context.type === 'issue' && props.context.links) {
    loadSerial(props.context.link);
  }

  if (props.context.type === 'template') {
    selectTemplate(props.templates[0]);
    allowSelectTemplate.value = false;
  }

  if (props.context?.step?.product_key) {
    loadProduct(props.context.step.product_key);
  }

  if (props.context?.serial?.product_key) {
    loadProduct(props.context.serial.product_key);
  }

  if (props.context?.workOrder?.product_key) {
    loadProduct(props.context.workOrder.product_key)
  }

  if (props.context?.serial?.wo_key) {
    loadWorkOrder(props.context?.serial?.wo_key);
  }

  if (props.context?.serial?._key) {
    loadSerial(props.context.serial._key);
  }
}

initialize();

/**
 * Loads serial data from the API and sets it in the context
 * @param {string} serial_key - The key/ID of the serial to load
 */
async function loadSerial(serial_key) {
  if (serial_key) {
    const { data } = await api.get(`serial/${serial_key}`);
    props.context.setSelectedSerial(data);
  } else {
    props.context.setSelectedSerial(null);
  }
}

/**
 * Loads product data from the API and sets it in the context
 * @param {string} product_key - The key/ID of the product to load
 */
async function loadProduct(product_key) {
  if (product_key) {
    const { data } = await api.get(`product/${product_key}`);
    props.context.setSelectedProduct(data);
  } else {
    props.context.setSelectedProduct(null);
  }
}

/**
 * Loads work order data from the API and sets it in the context
 * @param {string} wo_key - The key/ID of the work order to load
 */
async function loadWorkOrder(wo_key) {
  if (wo_key) {
    const { data } = await api.get(`work-order/${wo_key}`);
    props.context.setSelectedWorkOrder(data?.detail);
  } else {
    props.context.setSelectedWorkOrder(null);
  }
}

// async function loadBatchSerial(batch_key) {
//   const { data: batch_serials } = await api.get('serial-batch', {
//     params: {
//       batch_key: batch_key,
//     },
//   });
//   for (const serial of batch_serials) {
//     serialModelInitalValue.value.push({
//       value: serial._key,
//       _key: serial._key,
//       label:
//         serial.code ||
//         '(' + t('serial_code_to_be_assigned') + ' - ID ' + serial._key + ')',
//       wo_key: serial.wo_key,
//       product_key: serial.product_key,
//     });
//   }
//   if (serialModelInitalValue.value.length === 1) {
//     serialModel.value = serialModelInitalValue.value[0];
//     await loadSerial(serialModelInitalValue.value[0]._key);
//   }
// }

/**
 * Handles serial selection - loads the selected serial and re-selects the template
 * @param {Object} serial - The serial object containing _key property
 */
async function selectSerial(serial) {
  let serial_key = serial?._key;
  await loadSerial(serial_key);
  selectTemplate(selectedTemplateBK.value);
}


/**
 * Selects a print template and initializes the form model with field values
 * Fetches template data from API and maps field values from context (preset/custom values)
 * @param {Object} template - The template object containing _key property
 */
async function selectTemplate(template) {
  resetState();

  hasSerialLink.value = false;
  selectedTemplateBK.value = template;
  activeStep.value = 1;
  selectedTemplate.value = undefined;
  await nextTick();
  isLoadingTemplate.value = true;
  try {
    const { data } = await api.get(`print-template/${template._key}`);
    selectedTemplate.value = data;

    if (!data.template || !data.template.schemas) {
      throw new Error('Invalid template data: missing template or schemas');
    }

    const { fieldNames, getLink, getContent } = getFieldNamesAndLinks(data);
    currentGetLink = getLink;

    // Ensure custom fields are loaded — idempotent, safe to call every time
    await store.dispatch('getCustomFields');
    const allCustomFields = store.state.form.customFields;

    computedFieldDefs = [];
    computedFieldNames = new Set();
    templateExprFieldDefs = [];
    templateExprFieldNames = new Set();

    formModel = reactive(
      Object.fromEntries(
        fieldNames.map((fieldName) => {
          if (!fieldName || typeof fieldName !== 'string') {
            console.warn('Invalid field name found:', fieldName);
            return ['unknown_field', ''];
          }
          const link = getLink(fieldName);
          if (!link) {
            return [fieldName, getContent(fieldName)];
          }
          if (link.value && String(link.value).includes('serial')) {
            hasSerialLink.value = true;
          }
          if (link.type === 'computed') {
            computedFieldDefs.push({ name: fieldName, expression: link.templateExpression });
            computedFieldNames.add(fieldName);
            return [fieldName, ''];
          }
          if (link.type === 'template_expression') {
            const hasFieldRef = link.templateExpression?.includes('{{field::');
            if (hasFieldRef) {
              templateExprFieldDefs.push({ name: fieldName, expression: link.templateExpression });
              templateExprFieldNames.add(fieldName);
            }
            const resolved = resolveExpression(link.templateExpression, props.context, allCustomFields);
            return [fieldName, String(resolved ?? '')];
          }
          if (link.type === 'preset') {
            const presetValue = props.context.getPresetValue(link.value);
            return [fieldName, String(presetValue ?? '')];
          }
          const customValue = props.context.getCustomFieldValue(link.value);
          return [fieldName, String(customValue ?? '')];
        }),
      ),
    );

    const hasDerivedFields = computedFieldDefs.length > 0 || templateExprFieldDefs.length > 0;
    if (hasDerivedFields) {
      const derivedNames = new Set([...computedFieldNames, ...templateExprFieldNames]);
      const sourceFields = fieldNames.filter(n => !derivedNames.has(n));
      recomputeFields();
      stopComputedWatcher = watch(
        () => sourceFields.map(n => formModel[n]),
        recomputeFields,
      );
    }


  } catch (error) {
    console.error(error);
    window.alert(error.message);
  } finally {
    isLoadingTemplate.value = false;
  }
}

/**
 * Loads an image from a URL and converts it to base64 format
 * Validates the URL, fetches the image, and converts to base64 data URL
 * @param {string} url - The URL of the image to load
 * @returns {Promise<string>} Promise that resolves to base64 data URL of the image
 * @throws {Error} If URL is invalid, fetch fails, or file is not an image
 */
async function loadImage(url) {
  if (typeof url !== 'string') {
    throw new Error('Invalid image URL provided');
  }

  if (url.trim() === '' || [undefined, null].includes(url)) {
    console.warn('No image path provided for field', url);
    return '';
  }

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
    }

    const blob = await response.blob();

    if (!blob || blob.size === 0) {
      throw new Error('Empty or invalid image data received');
    }

    // Check if it's actually an image
    if (!blob.type.startsWith('image/')) {
      throw new Error(`Invalid file type: ${blob.type}. Expected an image.`);
    }

    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = function () {
        resolve(this.result);
      };
      reader.onerror = function () {
        reject(new Error('Failed to read image file'));
      };
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    throw new Error(`Image loading failed for URL "${url}": ${error.message}`);
  }
}

/**
 * Prepares input data for PDF generation by processing form fields
 * Converts image URLs to base64 and ensures all field values are properly formatted
 * @returns {Promise<Array<Object>>} Array of input objects for each page/schema in the template
 * @throws {Error} If template schemas are not available
 */
async function prepareInputs() {
  // Needed to parse input type to load images as base64
  const inputs = [];

  if (!selectedTemplate.value?.template?.schemas) {
    throw new Error('Template schemas are not available');
  }

  for (const pageSchema of selectedTemplate.value.template.schemas) {
    const fields = normalizePageSchema(pageSchema);
    const schemaFields = [];

    for (const field of fields) {
      const fieldName = field.name;
      if (!fieldName) continue;

      if (field.type === 'image') {
        try {
          const imageUrl = formModel[fieldName];
          const base64 = await loadImage(imageUrl);
          schemaFields.push([fieldName, base64]);
        } catch (err) {
          console.error(`Error loading image for field ${fieldName}:`, err);
          schemaFields.push([fieldName, '']);
        }
      } else {
        const link = currentGetLink?.(fieldName);
        const needsFreshResolve = link?.type === 'template_expression' && field.type !== 'text';
        if (needsFreshResolve) {
          const allCustomFields = store.state.form.customFields;
          const resolved = resolveExpression(link.templateExpression, props.context, allCustomFields, formModel);
          schemaFields.push([fieldName, String(resolved ?? '')]);
        } else {
          const fieldValue = formModel[fieldName];
          const safeValue = fieldValue != null ? String(fieldValue) : '';
          schemaFields.push([fieldName, safeValue]);
        }
      }
    }
    inputs.push(Object.fromEntries(schemaFields));
  }

  return inputs;
}

/**
 * Collects all required field names from the template.
 * @returns {string[]}
 */
function getRequiredFieldNames() {
  const template = selectedTemplate.value?.template;
  if (!template?.schemas || !Array.isArray(template.schemas)) return [];
  const names = [];
  for (const pageSchema of template.schemas) {
    for (const field of normalizePageSchema(pageSchema)) {
      if (field.name && field.required) names.push(field.name);
    }
  }
  return names;
}

/**
 * Generates a PDF preview using the selected template and form data
 * Validates template structure, prepares inputs, and generates PDF using @pdfme/generator
 * Sets the preview source for display and advances to the preview step
 */
async function goToPreview() {
  const requiredNames = getRequiredFieldNames();
  const requiredEmpty = requiredNames.filter((name) => {
    const v = formModel[name];
    return v === undefined || v === null || String(v).trim() === '';
  });
  if (requiredEmpty.length > 0) {
    window.alert(t('printDialog.requiredFieldsEmpty', { count: requiredEmpty.length }));
    return;
  }

  previewSrc.value = undefined;
  activeStep.value = 2;
  await nextTick();

  try {
    const { template } = selectedTemplate.value;

    // Validate template structure
    if (!template) {
      throw new Error('Template is undefined');
    }

    if (!template.schemas || !Array.isArray(template.schemas)) {
      throw new Error('Template schemas are missing or invalid');
    }

    const inputs = await prepareInputs();

    // Validate inputs structure
    if (!inputs || !Array.isArray(inputs)) {
      throw new Error('Inputs are missing or invalid');
    }

    const cleanSchemas = JSON.parse(JSON.stringify(schemasToV5(template.schemas)));

    // Migrate gs1datamatrix → datamatrix when the runtime value is not valid GS1 AI format.
    // This lets existing templates that used gs1datamatrix for free-form data render correctly.
    const gs1Regex = /\((01)\)(\d*)(\(|$)/;
    for (const page of cleanSchemas) {
      for (const field of page) {
        if (field.type !== 'gs1datamatrix') continue;
        const val = inputs[0]?.[field.name] ?? '';
        const m = val.match(gs1Regex);
        const isValidGs1 = m && val.length <= 52 && m[1] === '01' &&
          [8, 12, 13, 14].includes(m[2].length);
        if (!isValidGs1) {
          field.type = 'datamatrix';
        }
      }
    }

    const cleanTemplate = { basePdf: normalizeBasePdf(template.basePdf), schemas: cleanSchemas };

    previewSrc.value = await generate({
      template: cleanTemplate,
      inputs,
      plugins: pdfmePlugins,
    });
  } catch (error) {
    console.error('Error generating PDF preview:', error);
    window.alert(`PDF generation failed: ${error}\nPlease check the template configuration and try again.`);
    // Go back to the previous step
    activeStep.value = 1;
  }
}

function onCopiesConfirmed(value) {
  showCopiesPrompt.value = false;
  const copies = Math.max(1, parseInt(value, 10) || 1);
  sendToPrinter(copies);
}

async function sendToPrinter(copies = 1) {
  if (!selectedPrinter.value) return;
  isPrinting.value = true;

  try {
    const printer = selectedPrinter.value;
    let data;
    let format;

    if (printer.type === 'zpl') {
      const dpi = printer.dpi || 203;
      const offsetX = printer.offset_x || 0;
      const offsetY = printer.offset_y || 0;
      const inputs = await prepareInputs();
      const zplInputs = await processZplImageFields(
        schemasToV5(selectedTemplate.value.template.schemas),
        inputs,
        dpi,
      );
      const zplString = generateZpl(selectedTemplate.value.template, zplInputs, { dpi, quantity: copies, offsetX, offsetY });
      data = zplString;
      format = 'zpl';
    } else {
      // PDF path: generate → base64
      const { template } = selectedTemplate.value;
      const cleanSchemas = JSON.parse(JSON.stringify(schemasToV5(template.schemas)));
      // gs1datamatrix migration (same as goToPreview)
      const inputs = await prepareInputs();
      const gs1Regex = /\((01)\)(\d*)(\(|$)/;
      for (const page of cleanSchemas) {
        for (const field of page) {
          if (field.type !== 'gs1datamatrix') continue;
          const val = inputs[0]?.[field.name] ?? '';
          const m = val.match(gs1Regex);
          const isValidGs1 = m && val.length <= 52 && m[1] === '01' && [8, 12, 13, 14].includes(m[2].length);
          if (!isValidGs1) field.type = 'datamatrix';
        }
      }
      const cleanTemplate = { basePdf: normalizeBasePdf(template.basePdf), schemas: cleanSchemas };
      const pdfBytes = await generate({ template: cleanTemplate, inputs, plugins: pdfmePlugins });
      const bytes = new Uint8Array(pdfBytes);
      let binary = '';
      const chunkSize = 8192;
      for (let i = 0; i < bytes.length; i += chunkSize) {
        binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
      }
      data = btoa(binary);
      format = 'pdf';
    }

    const result = await sendToPrintService({ data, printer, format, copies });

    if (result.ok) {
      onDialogHide();
      Notify.create({ type: 'positive', color: 'theme-green', message: t('printDialog.sendToPrinter.success') });
    } else if (result.error === 'no_service' || result.error === 'internal') {
      Notify.create({ type: 'warning', color: 'theme-orange', message: t('printDialog.sendToPrinter.noService') });
    } else if (result.error === 'connection_refused') {
      Notify.create({ type: 'negative', color: 'theme-red', message: t('printDialog.sendToPrinter.connectionRefused') });
    } else if (result.error === 'timeout') {
      Notify.create({ type: 'warning', color: 'theme-orange', message: t('printDialog.sendToPrinter.timeout') });
    } else {
      Notify.create({ type: 'negative', color: 'theme-red', message: t('printDialog.sendToPrinter.error') });
    }
  } catch (err) {
    // POST failed or other error — stay open so user can retry
    isPrinting.value = false;
    Notify.create({ type: 'negative', color: 'theme-red', message: err.message || t('printDialog.sendToPrinter.error') });
    return;
  }
  isPrinting.value = false;
}

const dialogWidth = 615;
const scrollBarWidth = 15;
const contentPadding = 24 * 2;
const pdfWidth = dialogWidth - scrollBarWidth - contentPadding;
</script>
