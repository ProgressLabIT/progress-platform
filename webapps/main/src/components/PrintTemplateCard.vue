<template>
  <q-card square bordered class="surface2">
    <q-card-section class="row items-baseline">
      <q-icon name="mdi-file-document" size="sm" />
      <div class="q-ml-sm text-h3" :class="{ 'text-italic': template.temp }">
        <div>{{ template.name }}</div>
        <div v-if="template.trash" class="smaller">
          ({{ $capitalize($t('deleted')) }})
        </div>
        <div v-else-if="template.temp" class="smaller">
          ({{ $capitalize($t('unsaved')) }})
        </div>
      </div>
    </q-card-section>

    <q-card-section>
      {{ template.description }}
    </q-card-section>

    <q-card-section class="row justify-start items-center q-gutter-sm">
      <q-btn
        size="sm"
        flat
        round
        color="high"
        icon="mdi-file-search-outline"
        @click="showTemplatePreview"
      >
        <q-tooltip>{{ $capitalize($t('print_template_preview')) }}</q-tooltip>
      </q-btn>

      <q-btn
        v-if="allowEdit"
        flat
        round
        icon="mdi-printer"
        color="high"
        class="q-ml-sm"
        @click.stop="openPrintDialog"
      >
        <q-tooltip>{{ $capitalize($t('print')) }}</q-tooltip>
      </q-btn>

      <q-btn
        v-if="allowEdit"
        flat
        round
        size="sm"
        color="high"
        icon="mdi-pencil"
        @click="editTemplate"
      >
        <q-tooltip>{{ $capitalize($t('edit')) }}</q-tooltip>
      </q-btn>
      <q-btn
        v-if="allowDelete"
        flat
        round
        size="sm"
        color="high"
        icon="mdi-delete"
        @click="showDelete = true"
      >
        <q-tooltip>
          {{ $capitalize($t('delete')) }}
        </q-tooltip>
      </q-btn>

      <q-btn
        v-if="allowUnlink"
        flat
        round
        size="sm"
        color="high"
        icon="mdi-close"
        @click="showUnlink = true"
      >
        <q-tooltip>
          {{ $capitalize($t('unlink')) }}
        </q-tooltip>
      </q-btn>

      <slot name="extra-actions" />
    </q-card-section>

    <!-- DELETE CONFIRMATION -->
    <div
      v-if="showDelete"
      class="absolute-full surface1 column"
      :class="showImage ? 'q-pa-md' : 'q-pa-sm'"
    >
      <div class="display weight-medium q-mt-sm">
        {{ template.name }}
      </div>
      <div>
        {{
          $t('print_template_confirm_delete_question', {
            entities: template.entities ? template.entities : 0,
          })
        }}
      </div>
      <q-space />
      <div class="row justify-between">
        <q-btn color="theme-red" size="12px" @click.stop="deleteTemplate">
          {{ $t('confirm') }}
        </q-btn>
        <q-btn color="theme-grey" size="12px" @click.stop="showDelete = false">
          {{ $t('cancel') }}
        </q-btn>
      </div>
    </div>

    <!-- UNLINK CONFIRMATION -->
    <div
      v-if="showUnlink"
      class="absolute-full surface1 column"
      :class="showImage ? 'q-pa-md' : 'q-pa-sm'"
    >
      <div class="display weight-medium q-mt-sm">
        {{ template.name }}
      </div>
      <div>
        {{ $t('print_template_confirm_unlink_question') }}
      </div>
      <q-space />
      <div class="row justify-between">
        <q-btn color="theme-red" size="12px" @click.stop="unlinkTemplate">
          {{ $t('confirm') }}
        </q-btn>
        <q-btn color="theme-grey" size="12px" @click.stop="showUnlink = false">
          {{ $t('cancel') }}
        </q-btn>
      </div>
    </div>

    <PrintTemplateDesigner
      :show="templateToEdit !== null"
      :edit-template="templateToEdit"
      @close="resetDesigner"
      @saved="$emit('saved')"
    />

    <!-- PRINT FORM/PREVIEW -->
    <MediaViewer
      :show="!!showPreview"
      :media_name="showPreview?.name"
      :media_src="showPreview?.pdf"
      :is_pdf_stream="true"
      @close="showPreview = null"
    />
  </q-card>
</template>

<script>
import MediaViewer from '@/components/MediaViewer.vue';
import PrintTemplateDesigner from '@/components/PrintTemplateDesigner.vue';
import { usePrintDialog, generatePdf } from '@/lib/print';

export default {
  name: 'PrintTemplateCard',

  components: {
    MediaViewer,
    PrintTemplateDesigner,
  },

  props: {
    template: {
      type: Object,
      required: true,
    },

    allowEdit: {
      type: Boolean,
      default: false,
    },

    allowDelete: {
      type: Boolean,
      default: false,
    },

    allowUnlink: {
      type: Boolean,
      default: false,
    },
  },

  emits: ['saved', 'delete', 'restore', 'unlink'],

  setup(props) {
    const { open: openPrintDialog } = usePrintDialog({
      context: 'print_template',
      contextData: props.template._key,
    });
    return {
      openPrintDialog,
    };
  },

  data() {
    return {
      showPreview: false,
      showDelete: false,
      showUnlink: false,
      templateToEdit: null,
    };
  },

  methods: {
    async showTemplatePreview() {
      const {
        data: { template },
      } = await this.$api.get(`print-template/${this.template._key}`);
      const inputs = template.sampledata || [];
      this.showPreview = {
        name: template.name,
        pdf: await generatePdf({ template, inputs }),
      };
    },

    async editTemplate() {
      const { data } = await this.$api.get(
        `print-template/${this.template._key}`,
      );
      this.templateToEdit = data;
    },

    async deleteTemplate() {
      await this.$api
        .delete(`print-template/${this.template._key}`)
        .then(() => {
          this.showDelete = false;
          this.$emit('delete');
        });
    },

    async unlinkTemplate() {
      this.showUnlink = false;
      this.$emit('unlink');
    },

    resetDesigner() {
      this.templateToEdit = null;
    },
  },
};
</script>
