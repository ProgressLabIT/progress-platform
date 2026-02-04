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
                v-for="field in normalizePageSchema(pageSchema)"
                :key="field.name"
              >
                <template v-if="field.type === 'image'">
                  <div>{{ field.name }}</div>
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
                <q-input
                  v-else
                  v-model="formModel[field.name]"
                  :label="field.name"
                  filled
                />
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
        </q-stepper-navigation>
      </q-step>
    </q-stepper>
  </BaseDialog>
</template>

<script setup>
import { generate } from '@pdfme/generator';
import { useDialogPluginComponent } from 'quasar';
import { nextTick, ref, reactive, toRaw } from 'vue';
import VuePdfEmbed from 'vue-pdf-embed';
import { api } from '@/boot/axios';
import { linkedText, linkedImage, linkedBarcodes } from '@/plugins';
import BaseDialog from '@/components/BaseDialog.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import PrintTemplateCard from '@/components/PrintTemplateCard.vue';
import BaseAutocompleteSerial from './BaseAutocompleteSerial.vue';

const pdfmePlugins = {
  text: linkedText,
  image: linkedImage,
  qrcode: linkedBarcodes.qrcode,
  ean13: linkedBarcodes.ean13,
  code39: linkedBarcodes.code39,
  code128: linkedBarcodes.code128,
  gs1datamatrix: linkedBarcodes.gs1datamatrix,
  japanpost: linkedBarcodes.japanpost,
  nw7: linkedBarcodes.nw7,
  itf14: linkedBarcodes.itf14,
  upca: linkedBarcodes.upca,
  upce: linkedBarcodes.upce,
};

/** Normalize page schema to array of { name, type, ... } (v5 format). Supports v2/v4 (keyed object) and v5 (array). */
function normalizePageSchema(pageSchema) {
  if (!pageSchema) return [];
  if (Array.isArray(pageSchema)) return pageSchema;
  return Object.entries(pageSchema).map(([fieldName, fieldSpec]) => ({
    ...fieldSpec,
    name: fieldName,
  }));
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
  for (const pageSchema of schemas) {
    const fields = normalizePageSchema(pageSchema);
    for (const field of fields) {
      const name = field.name || field.key;
      if (name) {
        fieldNames.push(name);
        if (field.linkType && field.linkType !== 'none') {
          const value = field.linkType === 'preset' ? field.linkValue : field.customFieldKey;
          linkByField[name] = { type: field.linkType, value: value || '' };
        }
      }
    }
  }
  return {
    fieldNames: [...new Set(fieldNames)],
    getLink: (fieldName) => linkByField[fieldName] || null,
  };
}

/** Normalize full schemas to v5 (array of arrays) for generate(). */
function schemasToV5(schemas) {
  if (!schemas || !Array.isArray(schemas)) return [];
  return schemas.map(normalizePageSchema);
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

const { dialogRef, onDialogHide, onDialogOK, onDialogCancel } =
  useDialogPluginComponent();
// This can't be inside the template due to unwrapping
// See: https://github.com/vuejs/composition-api/issues/317#issuecomment-1069145915
const getDialogRef = () => dialogRef;

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

    const { fieldNames, getLink } = getFieldNamesAndLinks(data);

    formModel = reactive(
      Object.fromEntries(
        fieldNames.map((fieldName) => {
          if (!fieldName || typeof fieldName !== 'string') {
            console.warn('Invalid field name found:', fieldName);
            return ['unknown_field', ''];
          }
          const link = getLink(fieldName);
          if (!link) {
            return [fieldName, ''];
          }
          if (link.value && String(link.value).includes('serial')) {
            hasSerialLink.value = true;
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
        const fieldValue = formModel[fieldName];
        const safeValue = fieldValue != null ? String(fieldValue) : '';
        schemaFields.push([fieldName, safeValue]);
      }
    }
    inputs.push(Object.fromEntries(schemaFields));
  }

  return inputs;
}

/**
 * Generates a PDF preview using the selected template and form data
 * Validates template structure, prepares inputs, and generates PDF using @pdfme/generator
 * Sets the preview source for display and advances to the preview step
 */
async function goToPreview() {
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

    const cleanTemplate = {
      basePdf: template.basePdf,
      schemas: toRaw(schemasToV5(template.schemas)),
    };

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

const dialogWidth = 615;
const scrollBarWidth = 15;
const contentPadding = 24 * 2;
const pdfWidth = dialogWidth - scrollBarWidth - contentPadding;
</script>
