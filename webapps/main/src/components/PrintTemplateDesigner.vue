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

          <q-space />

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
import { computed, ref, watch, toRaw } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
import { linkedText, linkedImage, linkedBarcodes } from '@/plugins';
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

/** @type {import('@pdfme/ui').Designer} */
let designer;
function initDesigner() {
  const container = document.getElementById('pdf-designer');
  if (!container) return;

  const rawTemplate = workingTemplate.value.template;
  const schemasV5 = schemasToV5(rawTemplate.schemas);
  const cleanTemplate = {
    basePdf: rawTemplate.basePdf,
    schemas: toRaw(schemasV5),
  };

  designer = new Designer({
    domContainer: container,
    template: cleanTemplate,
    options: { lang: locale.value },
    plugins: pdfmePlugins,
  });

  designer.onChangeTemplate((template) => {
    workingTemplate.value.template = cloneDeep(template);
  });
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

function initTemplate() {
  if (props.editTemplate) {
    mode.value = 'edit';
    workingTemplate.value = cloneDeep(props.editTemplate);
  } else {
    mode.value = 'new';
    workingTemplate.value = cloneDeep(emptyTemplate.value);
  }
}

async function saveTemplate() {
  const templateFromDesigner = designer.getTemplate();
  await api.request({
    method: mode.value === 'new' ? 'POST' : 'PUT',
    url: 'print-template',
    data: {
      ...workingTemplate.value,
      template: templateFromDesigner,
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
