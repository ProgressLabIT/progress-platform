<template>
  <q-card square bordered class="surface2">
    <q-card-section class="row items-baseline">
      <q-icon class="" name="mdi-file-document" size="sm" />
      <div class="q-ml-sm text-h3" :class="{ 'text-italic': template.temp }">
        <div>{{ template.name }}</div>
        <div v-if="template.temp" class="smaller">
          ({{ $capitalize($t('unsaved')) }})
        </div>
      </div>
    </q-card-section>

    <q-card-section>
      {{ template.description }}
    </q-card-section>

    <q-card-section class="row justify-start q-gutter-sm">
      <q-btn
        size="sm"
        flat
        round
        icon="mdi-file-search-outline"
        @click="showTemplatePreview"
      />
      <q-btn
        v-if="allowEdit"
        flat
        round
        size="sm"
        icon="mdi-pencil"
        @click="editTemplate"
      />
      <!-- TODO: Implement delete method -->
      <q-btn
        v-if="allowDelete"
        flat
        round
        size="sm"
        icon="mdi-delete"
        @click="$emit('delete')"
      />
    </q-card-section>

    <PrintTemplateDesigner
      :show="edit_template !== null"
      :edit_template="edit_template"
      @close="resetDesigner"
      @saved="$emit('saved')"
    />

    <!-- PRINT FORM/PREVIEW -->
    <MediaViewer
      :show="!!show_preview"
      :media_name="show_preview?.name"
      :media_src="show_preview?.pdf"
      @close="show_preview = null"
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

  emits: ['saved', 'delete'],

  data() {
    return {
      show_preview: false,
      edit_template: null,
    };
  },

  methods: {
    async showTemplatePreview() {
      const {
        data: { template },
      } = await this.$api.get(`print-template/${this.template._key}`);
      const inputs = template.sampledata;
      this.show_preview = {
        name: template.name,
        pdf: await generate({ template, inputs }),
      };
    },

    async editTemplate() {
      const { data } = await this.$api.get(
        `print-template/${this.template._key}`,
      );
      this.edit_template = data;
      this.show_designer = true;
    },

    resetDesigner() {
      this.show_designer = false;
      this.edit_template = null;
    },
  },
};
</script>
