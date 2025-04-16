<template>
  <div class="row full-height q-pa-md">
    <!-- LEFT COLUMN -->
    <div class="col-4 column full-height q-pr-md">
      <!-- PRODUCT IMAGE -->
      <div
        class="relative-position col-auto"
        style="border: solid 1px rgba(255, 255, 255, 0.12); height: 30vh"
      >
        <q-img
          class="fit"
          :src="img_src"
          :style="product.active ? '' : 'filter:grayscale(1) brightness(.5)'"
          @mouseenter="over_image = true"
          @mouseleave="over_image = false"
        >
        </q-img>
        <div class="absolute-full column q-pa-md">
          <q-btn
            v-if="over_image && !editMode && !no_image"
            class="absolute-bottom-right q-ma-md"
            color="theme-grey"
            size="12px"
            @click.stop="showMedia('img')"
          >
            <q-icon name="mdi-magnify" />
          </q-btn>

          <template v-if="editMode">
            <div
              class="absolute-top text-center q-py-xs"
              style="background: rgba(0, 0, 0, 0.5)"
            >
              {{ $capitalize($t('product.update_image')) }}
            </div>

            <q-space />

            <div class="row">
              <q-btn
                v-if="new_image || new_image_url === 'deleted'"
                size="12px"
                color="theme-orange"
                @click="clearTempImg"
              >
                {{ $t('product.restore_image') }}
              </q-btn>
              <q-btn
                v-else-if="!no_image"
                size="12px"
                color="theme-red"
                @click="deleteImg"
              >
                <q-icon name="mdi-delete" />
              </q-btn>
              <q-space />
              <input
                ref="upload_img"
                type="file"
                style="display: none"
                accept="image/*"
                @change="updateImg($event.target.files[0])"
              />
              <q-btn
                size="12px"
                color="theme-grey"
                @click="$refs.upload_img.click()"
              >
                <q-icon name="mdi-upload" />
              </q-btn>
              <q-btn
                v-if="img_src !== ''"
                size="12px"
                color="theme-grey"
                class="q-ml-sm"
                @click.stop="showMedia('img')"
              >
                <q-icon name="mdi-magnify" />
              </q-btn>
            </div>
          </template>
        </div>

        <div v-if="no_image" class="column absolute-full flex-center">
          <q-icon size="xl" color="text-low" name="mdi-image-off-outline">
          </q-icon>
          <div>
            {{ $t('product.no_image') }}
          </div>
        </div>
      </div>

      <!-- PRODUCT CODE -->
      <div class="q-mt-lg col-auto">
        <div class="text-h4 weight-bold text-uppercase">
          {{ $t('product.code') }}
        </div>
        <div v-if="!editMode" class="text-h1 display highlight">
          {{ product.code }}
        </div>
        <q-input
          v-else
          filled
          dense
          :model-value="temp_code"
          class="input-uppercase q-mt-md"
          @update:model-value="
            (value) => updateField('code', value.toUpperCase())
          "
        >
        </q-input>
      </div>

      <!-- PRODUCT DESCRIPTION -->
      <div class="q-mt-lg col-auto">
        <div class="text-h4 weight-bold text-uppercase">
          {{ $t('description') }}
        </div>
        <div
          v-if="!editMode"
          class="text-h3 q-mt-xs"
          style="white-space: pre-line"
        >
          {{ product.description }}
        </div>
        <q-input
          v-else
          filled
          dense
          type="textarea"
          :model-value="temp_desc"
          class="q-mt-md"
          @update:model-value="(value) => updateField('description', value)"
        >
        </q-input>
      </div>

      <!-- PRODUCT TAGS -->
      <div class="q-mt-lg col-auto">
        <div class="text-h4 weight-bold text-uppercase">
          {{ $t('tag', 2) }}
        </div>

        <TagInput
          v-if="editMode"
          :model-value="product.tags"
          class="q-mt-md"
          @update:model-value="updateField('tags', $event)"
        />
        <div v-else class="q-mt-xs">
          <span v-if="product.tags?.length === 0" class="text-h3">-</span>
          <TagChips v-else :tags="product.tags" />
        </div>
      </div>

      <q-space />

      <!-- EDIT MODE ACTIONS -->
      <div class="col-auto">
        <q-btn
          v-if="!editMode"
          color="theme-blue"
          class="full-width"
          @click="activateEditMode"
        >
          {{ $t('edit') }}
        </q-btn>

        <div v-else>
          <q-btn
            class="full-width q-mb-sm"
            :loading="saving"
            color="theme-green"
            @click="saveChanges"
          >
            {{ $t('save') }}
          </q-btn>
          <q-btn
            class="full-width"
            color="theme-grey"
            :disabled="saving"
            @click="cancelChanges"
          >
            {{ $t('cancel') }}
          </q-btn>
        </div>
      </div>
    </div>
    <!-- END OF LEFT COLUMN -->

    <!-- MIDDLE SECTION -->

    <div class="col-4 q-px-md full-height">
      <!-- TRACEABILITY SETTING -->
      <q-card square class="surface2 q-px-sm q-pt-sm q-pb-md column no-wrap">
        <q-card-section>
          <div class="text-h5 display weight-bold text-uppercase col-auto">
            {{ $t('traceability') }}
          </div>
        </q-card-section>

        <!-- TRACEABILITY SWITCH -->
        <q-card-section>
          <q-toggle
            filled
            clearable
            emit-value
            map-options
            :model-value="!!product.traceability_level"
            :label="$t('traceability.enabled')"
            :disable="!editMode"
            @update:model-value="
              updateField('traceability_level', $event ? 'form_only' : null)
            "
          />
        </q-card-section>

        <q-card-section>
          <q-toggle
            v-if="!!product.traceability_level"
            filled
            clearable
            emit-value
            map-options
            :model-value="!!product.serial_code_on_creation"
            :label="$t('traceability.serial_code_on_creation')"
            :disable="!editMode"
            @update:model-value="
              (value) => updateField('serial_code_on_creation', value)
            "
          />
        </q-card-section>

        <!-- PRODUCT COUNTER -->
        <q-card-section>
          <div class="q-mt-lg col-auto">
            <div class="text-h5 weight-bold text-uppercase">
              {{ $t('counter') }}
            </div>
            <div class="row q-gutter-md items-center q-mt-xs">
              <div style="white-space: pre-line" class="text-body1">
                {{ counter_name || 'NA' }}
              </div>
              <q-btn-group>
                <q-btn
                  v-if="editMode"
                  size="sm"
                  flat
                  icon="mdi-pencil"
                  @click="show_counter_form = true"
                />
                <q-btn
                  v-if="editMode"
                  size="sm"
                  flat
                  icon="mdi-close"
                  @click="cleanCounter"
                />
              </q-btn-group>
              <div class="row justify-between items-baseline">
                <BaseTooltipIcon
                  v-if="!editMode"
                  icon="mdi-content-copy"
                  icon_size="xs"
                  :tooltip="$capitalize($t('copy'))"
                  :color="$theme.orange"
                  @icon-click="openMassCopyDialog"
                />
              </div>
            </div>
          </div>
        </q-card-section>

        <!-- PRINT TEMPLATES -->
        <q-card-section>
          <div class="q-mt-lg col-auto">
            <div class="text-h5 weight-bold text-uppercase">
              {{ $t('print_templates') }}
            </div>
            <div class="row q-gutter-md items-center q-mt-xs">
              <q-list class="col-shrink scroll">
                <q-item
                  v-for="(template, index) in product.print_templates"
                  :key="template._key"
                  :class="{ 'text-italic': template.temp }"
                  @mouseenter="over_print = template._key"
                  @mouseleave="over_print = null"
                >
                  <q-item-section>
                    <q-item-label
                      >{{ template.name }}
                      {{
                        template.temp
                          ? '(' + $capitalize($t('unsaved')) + ')'
                          : ''
                      }}</q-item-label
                    >
                    <q-item-label caption>{{
                      template.description
                    }}</q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <div class="row q-gutter-sm items-center">
                      <q-btn
                        v-show="over_print === template._key || editMode"
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
                        icon="mdi-delete"
                        class="hover-red"
                        @click.stop="deleteTemplate(index)"
                      >
                      </q-btn>
                    </div>
                  </q-item-section>
                </q-item>
              </q-list>
            </div>
          </div>
        </q-card-section>

        <BaseAutocompleteTemplate
          v-if="editMode"
          class="q-px-sm q-mt-md"
          :label="$t('print_template_add')"
          :selected="product.print_templates"
          @select="addTemplate"
        />
      </q-card>

      <!-- WAREHOUSE  -->
      <q-card
        v-if="config.enableInventoryManagement"
        square
        class="surface2 q-mt-md q-px-sm q-pt-sm q-pb-md column no-wrap"
        style="max-height: 100%"
      >
        <q-card-section
          class="text-h5 display weight-bold text-uppercase col-auto"
        >
          {{ $t('warehouse.title') }}
        </q-card-section>
        <q-card-section class="col scroll">
          <q-toggle
            filled
            clearable
            emit-value
            map-options
            :model-value="product.manage_inventory || false"
            :label="$t('warehouse.manage')"
            :disable="!editMode"
            @update:model-value="updateField('manage_inventory', $event)"
          />
          <!-- <q-toggle
            filled
            clearable
            emit-value
            map-options
            :model-value="product.allow_negative_inventory || false"
            :label="$t('warehouse.allow_negative')"
            :disable="!editMode"
            @update:model-value="
              updateField('allow_negative_inventory', $event)
            "
          /> -->
        </q-card-section>
      </q-card>
    </div>

    <!-- RIGHT COLUMN -->
    <div class="col-4 q-pl-md column full-height no-wrap">
      <!-- DOCS -->
      <div class="col-auto">
        <q-card
          square
          class="surface2 q-px-sm q-pt-sm q-pb-md col-shrink column no-wrap"
        >
          <q-card-section class="text-h5 display highlight col-auto">
            {{ $capitalize($t('document.label', 2)) }}
          </q-card-section>
          <q-list class="col-shrink scroll" dense>
            <q-item
              v-for="(doc, index) in docs"
              :key="index"
              clickable
              @click="showMedia(index)"
            >
              <q-item-section class="col" :class="{ 'text-italic': doc.temp }">
                <q-item-label>
                  {{ doc.name }}
                  {{ doc.temp ? '(' + $capitalize($t('unsaved')) + ')' : '' }}
                </q-item-label>
              </q-item-section>
              <q-item-section class="col-1">
                <div>
                  <q-btn
                    v-if="editMode"
                    flat
                    round
                    size="10px"
                    icon="mdi-close"
                    class="hover-red"
                    @click.stop="deleteDoc(index)"
                  >
                  </q-btn>
                </div>
              </q-item-section>
              <q-item-section class="col-auto text-right">
                {{ $bytes(doc.size) }}
              </q-item-section>
            </q-item>
          </q-list>

          <input
            ref="upload_doc"
            type="file"
            multiple
            style="display: none"
            accept="*"
            @change="addFiles($event.target.files)"
          />
          <q-btn
            v-if="editMode"
            flat
            class="full-width q-mt-md"
            color="theme-blue"
            @click="$refs.upload_doc.click()"
          >
            <span>{{ $t('document.add', 2) }}</span>
            <q-space />
            <q-icon name="mdi-paperclip" />
          </q-btn>
        </q-card>
      </div>

      <div class="col-auto q-mt-md">
        <q-card
          square
          class="surface2 q-px-sm q-pt-sm q-pb-md col-shrink column no-wrap"
        >
          <q-card-section class="text-h5 display highlight col-auto">
            {{ $capitalize($t('metadata')) }}
          </q-card-section>
          <q-card-section>
            <div
              v-for="(field, index) in product.metadata"
              :key="field.custom_field_key"
              class="row items-top"
            >
              <FormField
                :field="field"
                :root-path="`/media/product/${product_key}/meta/${field.custom_field_key}`"
                dense
                :disable="!editMode"
                class="col"
                @update="
                  (value) => updateMetadataField(field.custom_field_key, value)
                "
              />
              <div class="col-auto flex-center">
                <q-btn
                  v-if="editMode"
                  flat
                  round
                  size="10px"
                  icon="mdi-close"
                  class="hover-red q-mt-sm q-ml-sm"
                  @click="metadata.splice(index, 1)"
                />
              </div>
            </div>
          </q-card-section>
          <q-btn
            v-if="editMode"
            flat
            class="full-width q-mt-md"
            color="theme-blue"
            :disable="!editMode"
            @click="addField"
          >
            <span>{{ $t('field_add') }}</span>
            <q-space />
            <q-icon name="mdi-plus" />
          </q-btn>
        </q-card>

        <!-- PRODUCTION NOTES -->
        <q-card
          square
          class="surface2 q-mt-md q-px-sm q-pt-sm q-pb-md column no-wrap"
          style="max-height: 100%"
        >
          <q-card-section
            class="text-h5 display weight-bold text-uppercase col-auto"
          >
            {{ $t('notes_production') }}
          </q-card-section>
          <q-card-section class="col scroll">
            <div v-if="!editMode" style="white-space: pre-line">
              {{ temp_notes }}
            </div>
            <q-input
              v-else
              filled
              dense
              autogrow
              :readonly="!editMode"
              :model-value="temp_notes"
              style="max-height: 100%"
              @update:model-value="
                (value) => updateField('production_notes', value)
              "
            >
            </q-input>
          </q-card-section>
        </q-card>
      </div>

      <!-- DOCUMENT VIEWER -->
      <MediaViewer
        v-if="show_media >= 0 || show_media === 'img'"
        :show="show_media >= 0 || show_media === 'img'"
        v-bind="{ media_name, media_src }"
        @close="show_media = -1"
      >
        <template #context-title>
          {{ $t('product.code').toUpperCase() }}: {{ product.code }}
        </template>
      </MediaViewer>

      <!-- PRINT FORM/PREVIEW -->
      <MediaViewer
        :show="show_template !== null"
        :media_name="show_template?.name"
        :media_src="show_template?.pdf"
        :is_pdf_stream="true"
        @close="show_template = null"
      />
      <BaseDialog
        :show="show_counter_form"
        :no-backdrop-dismiss="false"
        @close="show_counter_form = false"
      >
        <CounterSearch @select="selectCounter" />
      </BaseDialog>
    </div>
  </div>
</template>

<script>
import { generate } from '@pdfme/generator';
import { Dialog, Notify } from 'quasar';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { useStore, mapState /*, mapActions */ } from 'vuex';
import { api } from '@/boot/axios';
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue';
import BaseDialog from '@/components/BaseDialog.vue';
// import BaseConfirmationDialog from '@/components/BaseConfirmationDialog.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';
import FormField from '@/components/FormField.vue';
import MediaViewer from '@/components/MediaViewer.vue';
import TagChips from '@/components/TagChips.vue';
import TagInput from '@/components/TagInput.vue';
import AddCustomFieldDialog from '@/components/process-steps/AddCustomFieldDialog.vue';
import { useConfigStore } from '@/stores/config';
import MassCopyToProductDialog from '../components/MassCopyToProductDialog.vue';
import CounterSearch from '../components/settings/counters/CounterSearch.vue';

export default {
  name: 'ProductHome',

  components: {
    // BaseConfirmationDialog,
    FormField,
    MediaViewer,
    BaseDialog,
    BaseAutocompleteTemplate,
    TagInput,
    TagChips,
    CounterSearch,
    BaseTooltipIcon,
  },

  emits: ['changesSaved', 'changesCanceled'],

  setup() {
    const { t } = useI18n();
    const store = useStore();
    const route = useRoute();

    const { config } = useConfigStore();

    function openMassCopyDialog() {
      const sourceProduct = store.getters.productData(route.params.product_key);
      Dialog.create({
        component: MassCopyToProductDialog,
        componentProps: {
          title: t('massCopyProcess.title.counter'),
          baseFilters: {
            excludeProductKey: sourceProduct._key,
          },
          defaultFilters: {
            tagsToInclude: sourceProduct.tags,
          },
        },
      }).onOk(async (selectedProducts) => {
        try {
          await api.post(`/product/${sourceProduct._key}/counter/copy`, {
            target_product_keys: selectedProducts.map(({ _key }) => _key),
          });
          Notify.create({
            type: 'positive',
            message: t('massCopyProcess.success.counter', {
              count: selectedProducts.length,
            }),
            color: 'theme-green',
          });
        } catch (error) {
          console.error(error);
          Notify.create({
            type: 'negative',
            message: t('massCopyProcess.error.counter'),
            color: 'theme-red',
          });
        }
      });
    }

    return {
      openMassCopyDialog,
      config,
    };
  },

  data() {
    return {
      over_image: false,
      saving: false,
      show_delete_confirmation: false,
      show_cancel_confirmation: false,
      show_save_confirmation: false,
      show_media: -1,
      new_files: null,
      new_image: null,
      new_image_url: '',
      no_image: false,
      show_template: null,
      over_print: null,
      show_counter_form: false,
      new_product_counter: null,
    };
  },

  computed: {
    product_key() {
      return this.$route.params.product_key;
    },

    ...mapState({
      product: (state) => state.product.temp,
      saved_product: (state) => state.product.saved,
    }),

    counter_name() {
      if (this.new_product_counter) {
        return this.new_product_counter.name;
      } else if (this.$store.state.product.temp.counter) {
        return this.$store.state.product.temp.counter.name;
      }
      return '';
    },

    editMode: {
      get() {
        return this.$store.state.product.edit_modes.product;
      },
      set(value) {
        this.$store.commit('TOGGLE_EDIT_MODE', { view: 'product', value });
      },
    },

    saved_img_path() {
      return `/media/product/${this.product_key}/image.jpg`;
    },

    img_src() {
      return this.new_image_url ? this.new_image_url : this.saved_img_path;
    },

    temp_code() {
      return this.product.code;
    },

    temp_desc() {
      return this.product.description;
    },

    temp_notes() {
      return this.product.production_notes;
    },

    docs() {
      return this.product.docs;
    },

    saved_docs() {
      return this.$store.state.product.saved.docs;
    },

    media_name() {
      if (this.show_media == -1) {
        return '';
      } else if (this.show_media === 'img') {
        return 'Product image';
      } else {
        return this.docs[this.show_media].name;
      }
    },

    media_src() {
      if (this.show_media === 'img') {
        return this.img_src;
      } else if (this.show_media >= 0) {
        const doc = this.docs[this.show_media];
        let path = '';

        if (doc.temp) {
          path = window.URL.createObjectURL(doc.data);
        } else {
          path = `/media/product/${this.product_key}/doc/${encodeURI(
            this.media_name,
          )}`;
        }

        return path;
      } else {
        return null;
      }
    },

    metadata: {
      get() {
        return this.product?.metadata || [];
      },
      set(value) {
        this.updateField('metadata', value);
      },
    },
  },

  watch: {
    img_src() {
      if (!this.img_src.startsWith('blob')) {
        let test = new XMLHttpRequest();
        test.open('HEAD', this.img_src, false);
        test.send();
        if (test.status === 404) {
          this.no_image = true;
        }
      }
    },
  },

  methods: {
    //...mapActions(['loadProductDetails']),

    // deltaPcString(p) {
    //   let pc_sign = p.delta_pc > 0 ? '+' : ''
    //   return '('.concat(pc_sign, p.delta_pc, '%)')
    // },

    activateEditMode() {
      this.temp_code = this.product.code;
      this.temp_desc = this.product.description;

      this.editMode = true;
    },

    updateImg(img) {
      // let url = this.new_image_url
      // if (url) window.URL.revokeObjectURL(url)
      this.new_image_url = window.URL.createObjectURL(img);
      this.new_image = img;
      this.no_image = false;
    },

    clearTempImg() {
      window.URL.revokeObjectURL(this.new_image_url);
      this.new_image_url = null;
      this.new_image = null;
      this.no_image = false;
    },

    deleteImg() {
      // this is a fake URL to make v-img show placeholder
      this.new_image_url = 'deleted';
    },

    updateField(field, value) {
      this.$store.commit('UPDATE_TEMP_PARAMETER', {
        param: field,
        new_value: value,
      });
    },

    selectCounter(counter) {
      this.new_product_counter = counter;
      this.product.counter_key = counter._key;
      this.show_counter_form = false;
    },

    cleanCounter() {
      this.new_product_counter = null;
      this.product.counter_key = null;
      this.$store.state.product.temp.counter = null;
    },

    addFiles(fileList) {
      for (const file of fileList) {
        const existingIndex = this.docs.findIndex(
          ({ name }) => name === file.name,
        );
        const isExisting = existingIndex !== -1;
        if (isExisting) {
          const replace = window.confirm(
            this.$capitalize(
              this.$t('product.alerts.doc_name_exists', 1, {
                filename: file.name,
              }),
            ),
          );
          if (!replace) {
            return;
          }

          this.$store.commit('DELETE_TEMP_DOC', existingIndex);
        }

        this.$store.commit('ADD_TEMP_DOC', { file, force: isExisting });
      }
    },

    deleteDoc(index) {
      this.$store.commit('DELETE_TEMP_DOC', index);
    },

    addTemplate(selection) {
      this.$store.commit('ADD_TEMP_PRODUCT_TEMPLATE', selection);
    },

    deleteTemplate(index) {
      this.$store.commit('DELETE_TEMP_PRODUCT_TEMPLATE', index);
    },

    showMedia(value) {
      this.show_media = value;
    },

    addField() {
      console.log(this.metadata.map((f) => f.custom_field_key));
      Dialog.create({
        component: AddCustomFieldDialog,
        componentProps: {
          excludeKeys: this.metadata.map((f) => f.custom_field_key),
        },
      }).onOk((customField) => {
        this.metadata = [
          ...this.metadata,
          {
            custom_field_key: customField._key,
            label: customField.default_label,
            hint: customField.default_hint,
          },
        ];
      });
    },

    updateMetadataField(custom_field_key, value) {
      this.metadata = this.metadata.map((field) => {
        return field.custom_field_key === custom_field_key
          ? { ...field, value }
          : field;
      });
    },

    async showTemplatePreview(t) {
      const {
        data: { template },
      } = await this.$api.get(`print-template/${t._key}`);
      const inputs = template.sampledata;
      this.show_template = {
        name: t.name,
        pdf: await generate({ template, inputs }),
      };
    },

    saveChanges() {
      this.saving = true;

      const old_doc_list = this.saved_product.docs;
      const new_doc_list = this.product.docs;
      const old_template_list = this.saved_product.print_templates;
      const new_template_list = this.product.print_templates;

      let product_update = {
        new_product_data: this.product,
        deleted_docs: old_doc_list.filter(
          (o) => !new_doc_list.some((n) => n.name === o.name),
        ),
        deleted_templates: old_template_list.filter(
          (o) => !new_template_list.some((n) => n._key === o._key),
        ),
        image: {
          new: this.new_image,
          delete: this.new_image_url === 'deleted',
        },
        tags: {
          add: this.product.tags.filter(
            (tag) =>
              !this.saved_product.tags.some(
                (savedTag) => savedTag._key === tag._key,
              ),
          ),
          remove: this.saved_product.tags.filter(
            (savedTag) =>
              !this.product.tags.some((tag) => tag._key === savedTag._key),
          ),
        },
      };

      if (new_doc_list) {
        product_update.new_docs = new_doc_list.filter((d) => 'temp' in d);
      }

      if (new_template_list) {
        product_update.new_templates = new_template_list.filter(
          (t) => 'temp' in t,
        );
      }

      this.$store
        .dispatch('saveProductChanges', product_update)
        .then(async () => {
          // Show progress long enough the let user notice something is going on
          // even if the update is instantaneous
          // setTimeout(() => {
          await this.$store.dispatch('loadProductDetails', this.product_key);
          this.$emit('changesSaved');
          this.editMode = false;
          this.clearTempImg();
          this.saving = false;
          // }, 1500)
        })
        .catch((err) => {
          window.alert(err);
        });
    },

    cancelChanges() {
      this.$store.commit('CANCEL_PRODUCT_CHANGES');
      this.$emit('changesCanceled');
      this.editMode = false;
    },

    // deleteProduct() {
    //   this.$store.dispatch('moveToTrash', this.product)
    //   this.$router.push({ name: 'productList' })
    // }
  },
};
</script>
