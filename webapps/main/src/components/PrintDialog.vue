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
            :work_order_key="context.step.work_order_key"
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
                <q-file
                  v-if="field.type === 'image'"
                  :label="fieldName"
                  hint="WIP"
                  readonly
                />
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
import { nextTick, onMounted, ref } from 'vue';
import VuePdfEmbed from 'vue-pdf-embed';
import { api } from '@/boot/axios';
import BaseDialog from '@/components/BaseDialog.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import PrintTemplateCard from '@/components/PrintTemplateCard.vue';
import BaseAutocompleteSerial from './BaseAutocompleteSerial.vue';

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

const selectedTemplate = ref();
const isLoadingTemplate = ref(false);
const formModel = ref();
const serialModel = ref();
const serialModelInitalValue = ref([]);
const hasSerialLink = ref(false);

const selectedTemplateBK = ref();

const serialTemplateLinks = [
  'serial',
  'serial_qt',
  'serial_create_date',
  'serial_create_time',
];

async function loadSerial(serial_key) {
  if (serial_key) {
    const { data } = await api.get(`serial/${serial_key}`);
    props.context.setSelectedSerial(data);
  } else {
    props.context.setSelectedSerial(null);
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
      label: serial.code,
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

  if (props.context.step.batch_key) {
    loadBatchSerial(props.context.step.batch_key);
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

    formModel.value = Object.fromEntries(
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
          String(props.context.getCustomFieldValue(link.value) ?? ''),
        ];
      }),
    );
  } catch (error) {
    console.error(error);
    window.alert(error.message);
  } finally {
    isLoadingTemplate.value = false;
  }
}

const previewSrc = ref();
async function goToPreview() {
  previewSrc.value = undefined;
  activeStep.value = 2;
  await nextTick();

  const { template } = selectedTemplate.value;
  previewSrc.value = await generate({
    template,
    inputs: [formModel.value],
  });
}

const dialogWidth = 615;
const scrollBarWidth = 15;
const contentPadding = 24 * 2;
const pdfWidth = dialogWidth - scrollBarWidth - contentPadding;
</script>
