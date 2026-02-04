<template>
  <SettingsSection
    v-slot="{ editMode }"
    :title="$t('print_templates')"
    :save-fn="save"
    @cancel="cancel"
  >
    <BaseAutocompleteTemplate
      v-if="editMode"
      class="q-px-sm q-mt-md"
      :label="$t('print_template_add')"
      :selected="print_templates"
      @select="addTemplate"
    />
    <q-list class="col-shrink scroll">
      <q-item
        v-for="(template, index) in print_templates"
        :key="template._key"
        :class="{ 'text-italic': template.temp }"
        @mouseenter="over_print = template._key"
        @mouseleave="over_print = null"
      >
        <q-item-section>
          <q-item-label
            >{{ template.name }}
            {{
              template.temp ? '(' + $capitalize($t('unsaved')) + ')' : ''
            }}</q-item-label
          >
          <q-item-label caption>{{ template.description }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <div class="row q-gutter-sm items-center">
            <q-btn
              flat
              round
              icon="mdi-file-search-outline"
              size="10px"
              @click="showTemplatePreview(template)"
            >
            </q-btn>
            <q-btn
              v-if="editMode"
              flat
              round
              size="10px"
              icon="mdi-close"
              class="hover-red"
              @click.stop="deleteTemplate(index)"
            >
            </q-btn>
          </div>
        </q-item-section>
      </q-item>
    </q-list>

    <MediaViewer
      :show="show_template !== null"
      :media_name="show_template?.name"
      :media_src="show_template?.pdf"
      :is_pdf_stream="true"
      @close="show_template = null"
    />
  </SettingsSection>
</template>

<script>
import { generate } from '@pdfme/generator';
import { mapState /*, mapActions */ } from 'vuex';
import { linkedText, linkedImage, linkedBarcodes } from '@/plugins';
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue';
import MediaViewer from '@/components/MediaViewer.vue';
import SettingsSection from '@/components/SettingsSection.vue';

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

function normalizePageSchema(pageSchema) {
  if (!pageSchema) return [];
  if (Array.isArray(pageSchema)) return pageSchema;
  return Object.entries(pageSchema).map(([fieldName, fieldSpec]) => ({ ...fieldSpec, name: fieldName }));
}

function schemasToV5(schemas) {
  if (!schemas || !Array.isArray(schemas)) return [];
  return schemas.map(normalizePageSchema);
}

export default {
  name: 'LabelPrintTemplates',

  components: {
    BaseAutocompleteTemplate,
    SettingsSection,
    MediaViewer,
  },

  data() {
    return {
      show_template: null,
    };
  },

  computed: {
    ...mapState({
      print_templates: (state) => state.warehouse.temp_print_templates,
      saved_templates: (state) => state.warehouse.saved_print_templates,
    }),
  },

  mounted() {
    this.loadPrintTemplates();
  },

  methods: {
    loadPrintTemplates() {
      this.$store.dispatch('loadPrintLabelTemplates');
    },

    async showTemplatePreview(t) {
      const {
        data: { template },
      } = await this.$api.get(`print-template/${t._key}`);
      const inputs = template.sampledata || [];
      const cleanTemplate = {
        basePdf: template.basePdf,
        schemas: schemasToV5(template.schemas),
      };
      this.show_template = {
        name: t.name,
        pdf: await generate({
          template: cleanTemplate,
          inputs,
          plugins: pdfmePlugins,
        }),
      };
    },

    addTemplate(selection) {
      this.$store.commit('ADD_TEMP_LABEL_PRINT_TEMPLATE', selection);
    },

    deleteTemplate(index) {
      this.$store.commit('DELETE_TEMP_LABEL_PRINT_TEMPLATE', index);
    },

    save() {
      const old_template_list = this.saved_templates;
      const new_template_list = this.print_templates;

      let deleted_template_list = old_template_list.filter(
        (o) => !new_template_list.some((n) => n._key === o._key),
      );

      let added_template_list = new_template_list.filter((t) => 'temp' in t);

      let params = {
        new_templates: added_template_list,
        deleted_templates: deleted_template_list,
      };

      this.$store.dispatch('savePrintTemplates', params).catch((err) => {
        window.alert(err);
      });
    },

    cancel() {
      this.loadPrintTemplates();
    },
  },
};
</script>
