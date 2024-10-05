<template>
  <div class="row full-height q-py-md">
    <div class="column full-height col-3 justify-between q-px-lg q-pb-sm">
      <div>
        <div class="text-h1 display highlight q-mb-xs">
          {{ product_metadata.code }}
        </div>
        <div>
          {{ product_metadata.description }}
        </div>
      </div>

      <div>
        <div class="text-h5 text-uppercase q-mb-lg">
          {{ $t('filter', 2) }}
        </div>
        <q-input
          v-model="search_text"
          dense
          placeholder="Codice o Descrizione"
          append-icon="mdi-magnify"
        >
        </q-input>
      </div>

      <q-btn v-if="!editMode" color="theme-blue" @click="toggleEdit">
        {{ $t('bom.edit') }}
      </q-btn>

      <div v-else class="column q-gutter-sm">
        <q-btn color="theme-green" :loading="saving" @click="saveChanges">
          {{ $t('save') }}
        </q-btn>
        <q-btn :disabled="saving" color="theme-grey" @click="cancelChanges">
          {{ $t('cancel') }}
        </q-btn>
      </div>
    </div>

    <div class="col-9 column full-height q-pr-md">
      <q-table
        id="product-bom"
        ref="bom"
        v-model:selected="delete_lines"
        square
        row-key="table_key"
        class="my-sticky-header-table col text-body1"
        card-class="surface2"
        wrap-cells
        virtual-scroll
        hide-no-data
        hide-bottom
        :selection="editMode ? 'multiple' : 'none'"
        table-header-class="low-text"
        :rows="filtered_bom"
        :columns="table_headers"
        :pagination="{ rowsPerPage: 0 }"
        :rows-per-page-options="[0]"
        :virtual-scroll-sticky-size-start="48"
      >
        <template #body-cell-traceability_mandatory="props">
          <q-td :props="props">
            <q-toggle
              v-if="props.row.traceability_level"
              :model-value="!!props.value"
              :disable="!editMode"
              @update:model-value="
                (value) => toggleMandatoryTraceability(props.rowIndex, value)
              "
            />
          </q-td>
        </template>

        <template #body-cell-code="{ value }">
          <div class="nowrap">{{ value }}</div>
        </template>
      </q-table>

      <!-- BOTTOM ROW -->
      <q-card class="col-auto surface2">
        <q-separator />
        <div
          class="row full-width items-center justify-between q-px-md"
          style="height: 48px"
        >
          <div class="col-4">
            <q-btn
              v-show="editMode"
              size="sm"
              padding="xs lg"
              color="theme-red"
              icon="mdi-delete"
              :label="$t('bom.delete_selected')"
              @click="removeBomLines"
            >
            </q-btn>
          </div>

          <div class="smaller col-4 text-center">
            {{ filtered_bom.length }} {{ $t('of') }} {{ temp_bom.length }}
            {{ $t('element', 2).toUpperCase() }}
          </div>

          <div class="col-4 row justify-end">
            <q-btn
              v-show="editMode"
              size="sm"
              padding="xm lg"
              color="theme-blue"
              icon="mdi-plus"
              :label="$t('bom.add_line')"
              @click="openItemSearch"
            >
            </q-btn>
          </div>
        </div>
      </q-card>
    </div>

    <BaseDialog :show="show_product_catalog">
      <q-card style="max-width: 700px" class="surface1 q-pa-md">
        <q-card-section class="display text-h3 highlight">
          {{ $t('add') }} {{ $t('product.label', 2) }}
        </q-card-section>
        <q-card-section>
          <div class="row q-col-gutter-md items-center">
            <q-select
              v-model="new_line_phase"
              class="col-4"
              use-input
              dense
              input-debounce="0"
              :options="filtered_process"
              :label="$capitalize($t('phase.short'))"
              option-label="alias"
              popup-content-class="text-capitalize"
              @filter="filterOperations"
            >
            </q-select>

            <!-- PRODUCT -->
            <BaseAutocompleteProduct
              :model-value="new_line_product"
              :label="$capitalize($t('code') + ' / ' + $t('description'))"
              input-class="text-capitalize"
              class="col-6"
              :filled="false"
              :loading="catalog_loading"
              use-input
              :dense="true"
              @select="(selection) => loadProduct(selection)"
            />

            <q-input
              v-model="new_line_qt"
              v-model.number="new_line_qt"
              dense
              class="col-2"
              type="number"
              step="1"
              min="1"
              :label="$t('quantity.short')"
            >
            </q-input>

            <q-toggle
              v-if="new_line_product?.traceability_level"
              v-model="new_line_traceability_mandatory"
              class="col-2"
              :label="$t('traceability.mandatory')"
            />
          </div>
        </q-card-section>
        <div class="row q-col-gutter-md q-pa-md">
          <div class="col-6">
            <q-btn
              class="full-width"
              color="theme-blue"
              :label="$t('add')"
              @click="addItem"
            >
            </q-btn>
          </div>
          <div class="col-6">
            <q-btn
              class="full-width"
              color="theme-grey"
              :label="$t('cancel')"
              @click="show_product_catalog = false"
            >
            </q-btn>
          </div>
        </div>
      </q-card>
    </BaseDialog>
  </div>
</template>

<script>
import { mapState } from 'vuex';

import { api } from '@/boot/axios.js';
import BaseDialog from '@/components/BaseDialog.vue';
import multiMatch from '@/lib/MultiFieldSearch.js';
import BaseAutocompleteProduct from 'components/BaseAutocompleteProduct.vue';
// import { throttle as _throttle } from 'lodash';

export default {
  name: 'ProductBoM',

  components: {
    BaseDialog,
    BaseAutocompleteProduct,
  },

  emits: ['changesSaved', 'changesCanceled'],

  data() {
    return {
      search_text: '',
      table_height: '83vh',
      delete_lines: [],
      show_product_catalog: false,
      catalog_loading: false,
      product_catalog: [],
      new_line_product: {},
      new_line_phase: {},
      new_line_qt: null,
      new_line_traceability_mandatory: null,
      show_cancel_confirmation: false,
      show_save_confirmation: false,
      saving: false,
      filtered_process: null,
      filtered_products: null,
    };
  },

  computed: {
    ...mapState({
      // product_metadata: state => state.product.temp,
      saved_bom: (state) => state.bom.saved,
      saved_process: (state) => state.process.saved,
    }),

    table_headers() {
      // TODO: refactor into mixin / composition function, used also in WorkSessionBom
      return [
        {
          name: 'component_code',
          field: 'component_code',
          label: this.$t('code').toUpperCase(),
          align: 'left',
        },
        {
          name: 'component_description',
          field: 'component_description',
          label: this.$t('description').toUpperCase(),
          align: 'left',
          style: 'width: 50%',
        },
        {
          name: 'phase_name',
          field: 'phase_name',
          label: this.$t('phase.short').toUpperCase(),
          align: 'left',
        },
        {
          name: 'qt',
          field: 'qt',
          label: this.$t('quantity.short').toUpperCase(),
        },
        {
          name: 'traceability_mandatory',
          field: 'traceability_mandatory',
          label: this.$t('traceability.mandatory').toUpperCase(),
        },
      ];
    },

    editMode: {
      get() {
        return this.$store.state.product.edit_modes.bom;
      },
      set(value) {
        this.$store.commit('TOGGLE_EDIT_MODE', { view: 'bom', value });
      },
    },

    product_key() {
      return this.$route.params.product_key;
    },

    product_metadata() {
      return this.$store.getters.productData(this.product_key);
    },

    temp_bom: {
      get() {
        return this.$store.state.bom.temp.map((i) => {
          return { ...i, table_key: i.component_key + i.phase_key };
        });
      },
      set(new_bom) {
        this.$store.commit('UPDATE_TEMP_BOM', new_bom);
      },
    },

    filtered_bom() {
      const fields_to_search = [
        'component_code',
        'component_description',
        'phase_name',
      ];
      return this.temp_bom.filter((line) => {
        return multiMatch(this.search_text, line, fields_to_search);
      });
    },
  },

  watch: {
    // Reset form when closing/opening modal
    show_product_catalog() {
      this.new_line_product = null;
      this.new_line_qt = null;
      this.new_line_phase = null;
      this.new_line_traceability_mandatory = null;
    },
  },

  mounted() {
    /* *
     * remove from container its padding and that of the column,
     * plus the footer height
     */
    this.filtered_process = [...this.saved_process];
    // const resizeTable = () => this.table_height = this.$refs.container.clientHeight - 24 - 52
    // resizeTable()
    // window.onresize = _throttle(resizeTable, 100)
  },

  methods: {
    toggleEdit() {
      if (this.editMode == false) {
        this.editMode = true;
      } else {
        this.editMode = false;
        this.delete_lines = [];
      }
    },

    toggleAll() {
      if (this.delete_lines.length) {
        this.delete_lines = [];
      } else {
        this.delete_lines = this.filtered_bom;
      }
    },

    openItemSearch() {
      this.catalog_loading = true;
      this.show_product_catalog = true;

      api.get('product').then((resp) => {
        this.product_catalog = resp.data.filter(
          (p) => p._key != this.product_key,
        );
      });
      this.catalog_loading = false;
    },

    filterOperations(value, update) {
      if (value === '') {
        update(() => {
          this.filtered_process = [...this.saved_process];
        });
        return;
      }
      update(() => {
        const needle = value.toLowerCase();
        this.filtered_process = this.saved_process.filter((o) => {
          const include = o.alias.toLowerCase().includes(needle);
          return include;
        });
      });
    },

    loadProduct(selection) {
      this.new_line_product = selection;
      if (this.new_line_product?.traceability_level) {
        this.new_line_traceability_mandatory = true;
      } else {
        this.new_line_traceability_mandatory = null;
      }
    },

    updateItemQt(table_key, qt) {
      let new_bom = [...this.temp_bom];
      new_bom.find((i) => i.table_key === table_key).qt = qt;
      this.$store.commit('UPDATE_TEMP_BOM', new_bom);
    },

    removeBomLines() {
      const lines_to_delete = this.delete_lines.map((l) => l.table_key);
      const new_bom = this.temp_bom.filter(
        (line) => !lines_to_delete.includes(line.table_key),
      );
      this.$store.commit('UPDATE_TEMP_BOM', new_bom);
      this.delete_lines = [];
    },

    async addItem() {
      const is_duplicate = this.temp_bom.some((line) => {
        return (
          line.component_key == this.new_line_product._key &&
          (line.phase_key == this.new_line_phase?._key ?? null)
        );
      });

      if (!this.new_line_qt || this.new_line_qt <= 0) {
        window.alert(this.$capitalize(this.$t('bom.alerts.quantity_negative')));
      } else if (!is_duplicate) {
        const new_line = {
          /**
           * Cannot simply add ...new_line because it would
           * contain an _id field that, when sent to the db would refer
           * to the relationship and raise an error.
           */
          component_key: this.new_line_product._key,
          component_code: this.new_line_product.code,
          component_description: this.new_line_product.description,
          traceability_mandatory: this.new_line_traceability_mandatory,
          qt: this.new_line_qt,
          phase_name: this.new_line_phase?.alias ?? null,
          phase_key: this.new_line_phase?._key ?? null,
          table_key:
            this.new_line_product._key + this.new_line_phase?._key ?? null,
        };

        this.temp_bom = [...this.temp_bom, new_line];
        this.show_product_catalog = false;
      } else {
        window.alert(this.$capitalize(this.$t('bom.alerts.line_exists')));
      }
    },

    toggleMandatoryTraceability(lineIndex, value) {
      let temp_item = this.temp_bom[lineIndex];
      temp_item.traceability_mandatory = value;
      this.temp_bom = this.temp_bom.toSpliced(lineIndex, 1, temp_item);
    },

    cancelChanges() {
      this.temp_bom = [...this.saved_bom];
      this.editMode = false;
      this.delete_lines = [];
      this.$emit('changesCanceled');
    },

    saveChanges() {
      this.saving = true;
      const action_payload = {
        product_key: this.product_key,
        new_bom: this.temp_bom,
      };
      this.$store
        .dispatch('saveBomChanges', action_payload)
        .then(() => {
          setTimeout(() => {
            this.saving = false;
            this.editMode = false;
            this.$emit('changesSaved');
          }, 1500);
        })
        .catch((err) => {
          if (err.response.status == 403) {
            const api_resp = err.response.data.detail;
            const error_message =
              api_resp.message + '\n\nLoops:\n' + api_resp.data.join('\n');
            window.alert(error_message);
          } else {
            window.alert(err);
          }
          this.saving = false;
        });
    },
  },
};
</script>

<style lang="sass">
#product-bom
  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-2)

  tbody:last-child .absolute-bottom
    background-color: var(--surface-2)
    z-index: 999
</style>
