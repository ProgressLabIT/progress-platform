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
        icon="mdi-file-search-outline"
        @click="showTemplatePreview"
      >
        <q-tooltip>{{ $capitalize($t('print_template_preview')) }}</q-tooltip>
      </q-btn>
      <q-btn
        v-if="allowEdit"
        flat
        round
        size="sm"
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
        :icon="template.trash ? 'mdi-restore' : 'mdi-delete'"
        @click="template.trash ? $emit('restore') : $emit('delete')"
      >
        <q-tooltip>
          {{ $capitalize(template.trash ? $t('restore') : $t('delete')) }}
        </q-tooltip>
      </q-btn>

      <slot name="extra-actions" />
    </q-card-section>

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
      @close="showPreview = null"
    />
  </q-card>
</template>

<script>
import { generate } from '@pdfme/generator';
import MediaViewer from '@/components/MediaViewer.vue';
import PrintTemplateDesigner from '@/components/PrintTemplateDesigner.vue';

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
  },

  emits: ['saved', 'delete', 'restore'],

  data() {
    return {
      showPreview: false,
      templateToEdit: null,
    };
  },

  methods: {
    async showTemplatePreview() {
      const {
        data: { template },
      } = await this.$api.get(`print-template/${this.template._key}`);
      const inputs = template.sampledata;
      this.showPreview = {
        name: template.name,
        pdf: await generate({ template, inputs }),
      };
    },

    async editTemplate() {
      const { data } = await this.$api.get(
        `print-template/${this.template._key}`,
      );
      this.templateToEdit = data;
    },

    resetDesigner() {
      this.templateToEdit = null;
    },
  },
};
</script>
