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
          <BaseAutocompleteSerial
            v-if="context.type === 'step' && hasSerialLink"
            v-model="serialModel"
            :initial_values="serialModelInitalValue"
            :can_search="serialModelInitalValue.length <= 0"
            :label="$capitalize($t('serial'))"
            :disable="serialModelInitalValue.length === 1"
            :batch_key="context.step.batch_key"
            @select="selectSerial"
          >
          </BaseAutocompleteSerial>
          <template
            v-for="(pageSchema, index) in selectedTemplate.template.schemas"
            :key="index"
          >
            <fieldset
              v-if="Object.keys(pageSchema).length > 0"
              class="q-pa-md q-my-md column"
              style="gap: 16px"
            >
              <legend class="text-h5 q-px-sm">
                {{ $t('printDialog.fillData.page', { number: index + 1 }) }}
              </legend>

              <template
                v-for="(field, fieldName) in pageSchema"
                :key="fieldName"
              >
                <!-- TODO: Handle field type 'image' -->
                <template v-if="field.type === 'image'">
                  <div>{{ fieldName }}</div>
                  <q-img
                    :src="formModel[fieldName]"
                    fit="contain"
                    style="width: 200px"
                  />
                </template>
                <q-input
                  v-else
                  v-model="formModel[fieldName]"
                  :label="fieldName"
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

          <q-btn :label="$t('back')" color="theme-grey" @click="activeStep--" />
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
import { nextTick, onMounted, ref, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import VuePdfEmbed from 'vue-pdf-embed';
import { api } from '@/boot/axios';
import BaseDialog from '@/components/BaseDialog.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import PrintTemplateCard from '@/components/PrintTemplateCard.vue';
import BaseAutocompleteSerial from './BaseAutocompleteSerial.vue';

const { t } = useI18n();
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
const serialModel = ref();
const serialModelInitalValue = ref([]);
const hasSerialLink = ref(false);

const selectedTemplateBK = ref();

const serialTemplateLinks = [
  'serial.code',
  'serial.qt',
  'serial.create_date',
  'serial.create_time',
];

async function loadSerial(serial_key) {
  if (serial_key) {
    const { data } = await api.get(`serial/${serial_key}`);
    props.context.setSelectedSerial(data);
  } else {
    props.context.setSelectedSerial(null);
  }
}

async function loadProduct(product_key) {
  if (product_key) {
    const { data } = await api.get(`product/${product_key}`);
    props.context.setSelectedProduct(data);
  } else {
    props.context.setSelectedProduct(null);
  }
}

async function loadWorkOrder(wo_key) {
  if (wo_key) {
    const { data } = await api.get(`work-order/${wo_key}`);
    props.context.setSelectedWorkOrder(data?.detail);
  } else {
    props.context.setSelectedWorkOrder(null);
  }
}

async function loadBatchSerial(batch_key) {
  const { data: batch_serials } = await api.get('serial-batch', {
    params: {
      batch_key: batch_key,
    },
  });
  for (const serial of batch_serials) {
    serialModelInitalValue.value.push({
      value: serial._key,
      _key: serial._key,
      label:
        serial.code ||
        '(' + t('serial_code_to_be_assigned') + ' - ID ' + serial._key + ')',
      wo_key: serial.wo_key,
      product_key: serial.product_key,
    });
  }
  if (serialModelInitalValue.value.length === 1) {
    serialModel.value = serialModelInitalValue.value[0];
    await loadSerial(serialModelInitalValue.value[0]._key);
  }
}

async function selectSerial(serial) {
  let serial_key = serial?._key;
  await loadSerial(serial_key);
  selectTemplate(selectedTemplateBK.value);
}

onMounted(() => {
  //TODO: va verificato
  if (props.context.type === 'issue' && props.context.links) {
    loadSerial(props.context.link);
  }

  if (props.context.type === 'template') {
    selectTemplate(props.templates[0]);
    allowSelectTemplate.value = false;
  }

  if (props.context?.batch?._key) {
    loadBatchSerial(props.context.batch._key);
  }

  if (props.context?.step?.product_key) {
    loadProduct(props.context.step.product_key);
  }

  if (props.context?.serial?.product_key) {
    loadProduct(props.context.serial.product_key);
  }

  if (props.context?.serial?.wo_key) {
    loadWorkOrder(props.context?.serial?.wo_key);
  }

  if (props.context?.serial?._key) {
    loadSerial(props.context.serial._key);
  }
});

async function selectTemplate(template) {
  hasSerialLink.value = false;
  selectedTemplateBK.value = template;
  activeStep.value = 1;
  selectedTemplate.value = undefined;
  await nextTick();
  isLoadingTemplate.value = true;
  try {
    const { data } = await api.get(`print-template/${template._key}`);
    selectedTemplate.value = data;

    formModel = reactive(
      Object.fromEntries(
        data.template.columns.map((fieldName) => {
          const link = data.links[fieldName];
          if (!link) {
            return [fieldName, ''];
          }

          if (serialTemplateLinks.includes(link.value)) {
            hasSerialLink.value = true;
          }

          if (link.type === 'preset') {
            return [
              fieldName,
              String(props.context.getPresetValue(link.value) ?? ''),
            ];
          }

          return [
            fieldName,
            props.context.getCustomFieldValue(link.value) ?? undefined,
          ];
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

async function loadImage(url) {
  const response = await fetch(url);
  const blob = await response.blob();
  return new Promise((onSuccess) => {
    const reader = new FileReader();
    reader.onload = function () {
      onSuccess(this.result);
    };
    reader.readAsDataURL(blob);
  });
}

async function prepareInputs() {
  // Needed to parse input type to load images as base64
  const inputs = [];
  for (const schema of selectedTemplate.value.template.schemas) {
    let schemaFields = [];
    for (const [fieldName, fieldProps] of Object.entries(schema)) {
      if (fieldProps.type === 'image') {
        try {
          const base64 = formModel[fieldName] // Image URL
            ? await loadImage(formModel[fieldName])
            : ''; // empty string will not render any image. Background, if present, will be visibile.
          schemaFields.push([fieldName, base64]);
        } catch (err) {
          window.alert(
            'Error while generating the image. Please contact the system administrator.',
          );
          console.log(err);
        }
      } else {
        schemaFields.push([fieldName, formModel[fieldName]]);
      }
    }
    inputs.push(Object.fromEntries(schemaFields));
  }
  return inputs;
}

const previewSrc = ref();
async function goToPreview() {
  previewSrc.value = undefined;
  activeStep.value = 2;
  await nextTick();

  const { template } = selectedTemplate.value;
  const inputs = await prepareInputs();
  previewSrc.value = await generate({
    template,
    inputs,
  });
}

const dialogWidth = 615;
const scrollBarWidth = 15;
const contentPadding = 24 * 2;
const pdfWidth = dialogWidth - scrollBarWidth - contentPadding;
</script>
