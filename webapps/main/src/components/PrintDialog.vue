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
        <LoadingSignal v-if="isLoading" />
        <q-card-section v-else-if="templates.length === 0" class="text-center">
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
                flat
                round
                dense
                size="md"
                icon="mdi-check-circle"
                color="primary"
                @click="selectTemplate(template)"
              >
                <q-tooltip>{{ $capitalize($t('select')) }}</q-tooltip>
              </q-btn>
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
          <fieldset
            v-for="(pageSchema, index) in selectedTemplate.template.schemas"
            :key="index"
            class="q-pa-md q-my-md column"
            style="gap: 16px"
          >
            <legend class="text-h5 q-px-sm">
              {{ $t('printDialog.fillData.page', { number: index + 1 }) }}
            </legend>

            <template v-if="Object.keys(pageSchema).length === 0">
              <div class="text-h6 text-low">
                {{ $t('printDialog.fillData.noFields') }}
              </div>
            </template>

            <template v-for="(field, fieldName) in pageSchema" :key="fieldName">
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

        <q-stepper-navigation class="flex q-gutter-sm">
          <q-btn
            :label="$t('cancel')"
            color="theme-grey"
            @click="onDialogCancel"
          />

          <q-space />

          <q-btn
            :label="$t('back')"
            color="theme-black"
            @click="activeStep--"
          />
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

          <q-btn
            :label="$t('back')"
            color="theme-black"
            @click="activeStep--"
          />
          <q-btn
            :label="$t('print')"
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
import { nextTick, ref } from 'vue';
import VuePdfEmbed from 'vue-pdf-embed';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import BaseDialog from '@/components/BaseDialog.vue';
import LoadingSignal from '@/components/LoadingSignal.vue';
import PrintTemplateCard from '@/components/PrintTemplateCard.vue';
import { usePrintTemplates } from '@/composables/print-template';

const props = defineProps({
  context: {
    type: String,
    required: true,
    validator: (value) =>
      ['product', 'phase', 'step', 'issue_type'].includes(value),
  },
  contextData: {
    type: Object,
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

const { templates, isLoading } = usePrintTemplates({
  context: props.context,
  contextKey: props.contextData._key,
});

const selectedTemplate = ref();
const isLoadingTemplate = ref(false);
const formModel = ref();
async function selectTemplate(template) {
  activeStep.value = 1;
  selectedTemplate.value = undefined;
  await nextTick();
  isLoadingTemplate.value = true;
  try {
    const { data } = await api.get(`print-template/${template._key}`);
    selectedTemplate.value = data;

    formModel.value = Object.fromEntries(
      data.template.columns.map((fieldName) => [
        fieldName,
        String(getMappedValue(data.presets[fieldName]) ?? ''),
      ]),
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

const extractDate = (datetime) => new Date(datetime).toLocaleDateString();
const extractTime = (datetime) => new Date(datetime).toLocaleTimeString();

const store = useStore();
// TODO: not all parameters may will work with all contexts
function getMappedValue(presetName) {
  const job = store.state.traceability.working_job_data;
  const batch = store.state.traceability.current_batch_data;

  // TODO: Use a different date time format (?)
  switch (presetName) {
    case 'current_date':
      return new Date().toLocaleDateString();
    case 'current_time':
      return new Date().toLocaleTimeString();
    case 'current_user':
      return store.state.auth.user.name;

    case 'job_key':
      return job._key;
    case 'job_qt_planned':
      return job.qt_planned;
    case 'job_qt_completed':
      return job.qt_completed;
    case 'job_phase_alias':
      return job.phase_alias;
    case 'job_start_date':
      return extractDate(job.start);
    case 'job_start_time':
      return extractTime(job.start);
    case 'job_end_date':
      return extractDate(job.end);
    case 'job_end_time':
      return extractTime(job.end);

    case 'project_code':
      return job.project_code;
    case 'work_order_code':
      return job.wo_code;
    case 'work_order_qt_planned':
      return batch.qt_planned;
    case 'work_order_qt_completed':
      return batch.qt_completed;
    case 'work_order_start_date':
      return extractDate(batch.start);
    case 'work_order_start_time':
      return extractTime(batch.start);
    case 'work_order_end_date':
      return extractDate(batch.end);
    case 'work_order_end_time':
      return extractTime(batch.end);

    case 'product_code':
      return job.product_code;
    case 'product_description':
      return job.product_description;

    case 'issue_open_date':
      return extractDate(props.contextData.open_date);
    case 'issue_open_time':
      return extractTime(props.contextData.open_date);
    case 'issue_open_user':
      return props.contextData.open_user;
    case 'issue_close_date':
      return extractDate(props.contextData.close_date);
    case 'issue_close_time':
      return extractTime(props.contextData.close_date);
    case 'issue_close_user':
      return props.contextData.close_user;
    case 'issue_status':
      return props.contextData.status;
  }
}
</script>
