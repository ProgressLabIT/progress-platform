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
          <span v-if="product.tags && product.tags.length === 0" class="text-h3"
            >-</span
          >
          <TagChips v-else :tags="product.tags" />
        </div>

        <!-- TRACEABILITY SETTING TAGS -->
        <div class="q-mt-lg col-auto">
          <div class="text-h4 weight-bold text-uppercase">
            {{ $t('traceability', 2) }}
          </div>

          <q-select
            :options="traceability_options"
            filled
            clearable
            emit-value
            map-options
            :model-value="product.traceability_level"
            :label="$t('traceability.enabled')"
            :disabled="editMode"
            @update:model-value="updateField('traceability_level', $event)"
          />
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

    <!-- RIGHT SECTION -->

    <!-- NOTES -->
    <div class="col-4 q-px-md full-height">
      <!-- PRODUCT COUNTER -->
      <q-card-section>
        <div class="q-mt-lg col-auto">
          <div class="text-h4 weight-bold text-uppercase">
            {{ $t('counter') }}
          </div>
          <div
            v-if="!editMode"
            class="text-h3 q-mt-xs"
            style="white-space: pre-line"
          >
            {{ counter_name }}
          </div>
          <q-input
            v-else
            :model-value="counter_name"
            dense
            :label="$capitalize($t('counter'))"
            class="input-uppercase"
            clearable
            :readonly="!editMode"
            @click="show_counter_form = true"
          >
          </q-input>
        </div>
      </q-card-section>
      <q-card
        square
        class="surface2 q-px-sm q-pt-sm q-pb-md column no-wrap"
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

    <!-- RIGHT COLUMN -->
    <div class="col-4 q-pl-md column full-height no-wrap">
      <!-- DOCS -->
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
          accept="application/pdf, image/*"
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

      <!-- TODO: Enable after templates are being utilized somewhere -->
      <!-- PRINT TEMPLATES -->
      <q-card
        v-if="false"
        square
        class="surface2 q-px-sm q-pt-sm q-pb-md q-mt-lg col-shrink column no-wrap"
      >
        <q-card-section class="text-h5 display highlight col-auto">
          STAMPE ORDINE
        </q-card-section>
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
                  template.temp ? '(' + $capitalize($t('unsaved')) + ')' : ''
                }}</q-item-label
              >
              <q-item-label caption>{{ template.description }}</q-item-label>
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
                  icon="mdi-close"
                  class="hover-red"
                  @click.stop="deleteTemplate(index)"
                >
                </q-btn>
              </div>
            </q-item-section>
          </q-item>
        </q-list>

        <BaseAutocompleteTemplate
          v-if="editMode"
          class="q-px-sm q-mt-md"
          :label="$t('print_template_add')"
          :selected="product.print_templates"
          @select="addTemplate"
        />
      </q-card>

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
        @close="show_template = null"
      />

      <BaseDialog :show="show_counter_form" :no-backdrop-dismiss="false">
        <CounterSearch
          @close="show_counter_form = false"
          @select="selectCounter"
        >
        </CounterSearch>
      </BaseDialog>
    </div>
  </div>
</template>

<script>
import { generate } from '@pdfme/generator';
import { mapState, mapActions } from 'vuex';
import BaseAutocompleteTemplate from '@/components/BaseAutocompleteTemplate.vue';
// import BaseConfirmationDialog from '@/components/BaseConfirmationDialog.vue'
import BaseDialog from '@/components/BaseDialog.vue';
import MediaViewer from '@/components/MediaViewer.vue';
import TagInput from '@/components/TagInput.vue';
import TagChips from '../components/TagChips.vue';
import CounterSearch from '../components/settings/counters/CounterSearch.vue';

export default {
  name: 'ProductHome',

  components: {
    // BaseConfirmationDialog,
    MediaViewer,
    BaseAutocompleteTemplate,
    TagInput,
    TagChips,
    BaseDialog,
    CounterSearch,
  },

  emits: ['changesSaved', 'changesCanceled'],

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

    traceability_options() {
      return [
        {
          value: 'none',
          label: this.$t('traceability.options.none'),
        },
        {
          value: 'form_only',
          label: this.$t('traceability.options.form_only'),
        },
        {
          value: 'complete',
          label: this.$t('traceability.options.complete'),
        },
      ];
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
    ...mapActions(['loadProductDetails']),

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
      this.product.counter_id = counter._key;
      this.show_counter_form = false;
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
