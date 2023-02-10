<template>
  <div class="row full-height q-pa-lg">
    <div class="column col-3 justify-between q-pr-lg">

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
          dense
          placeholder="Codice o Descrizione"
          v-model="search_text"
          append-icon="mdi-magnify">
        </q-input>
      </div>

      <q-btn
        v-if="!edit_mode"
        @click="toggleEdit"
        color="theme-blue">
        {{ $t('bom.edit') }}
      </q-btn>

      <div v-else class="column q-gutter-sm">
        <q-btn
          color="theme-green"
          @click="saveChanges"
          :loading="saving">
          {{ $t('save') }}
        </q-btn>
        <q-btn
          :disabled="saving"
          color="theme-grey"
          @click="cancelChanges">
          {{ $t('cancel') }}
        </q-btn>
      </div>
    </div>

    <div class="col-9 column">
      <q-table
        square
        id="bom"
        ref="bom"
        row-key="table_key"
        class="my-sticky-header-table col text-body1"
        card-class="surface2"
        wrap-cells
        virtual-scroll
        :selection="edit_mode ? 'multiple' : 'none'"
        table-header-class="low-text"
        v-model:selected="delete_lines"
        :rows="filtered_bom"
        :columns="table_headers"
        :pagination="{ rowsPerPage: 0 }"
        :rows-per-page-options="[0]"
        :virtual-scroll-sticky-size-start="48"
        hide-bottom>
        <template #body-cell-code="{ value }">
          <div class="nowrap">{{ value }}</div>
        </template>

        <template #bottom-row>
          <div class="absolute-bottom">
          <q-separator></q-separator>
          <div
            class="row full-width items-center justify-between q-px-md"
            style="height: 48px">
            <div class="col-4">
              <q-btn
                v-show="edit_mode"
                size="sm"
                padding="xs lg"
                color="theme-red"
                icon="mdi-delete"
                :label="$t('bom.delete_selected')"
                @click="removeBomLines">
              </q-btn>
            </div>

            <div class="smaller col-4 text-center">
              {{ filtered_bom.length }} {{ $t('of') }} {{ temp_bom.length }} {{ $t('element', 2).toUpperCase() }}
            </div>

            <div class="col-4 row justify-end">
              <q-btn
                v-show="edit_mode"
                size="sm"
                padding="xm lg"
                color="theme-blue"
                icon="mdi-plus"
                :label="$t('bom.add_line')"
                @click="openItemSearch">
              </q-btn>
            </div>
          </div>
          </div>
        </template>
      </q-table>
    </div>
  </div>

  <BaseDialog :show="show_product_catalog">
    <q-card style="max-width: 700px;" class="surface1 q-pa-md">
      <q-card-section class="display text-h3 highlight">
        {{ $t('add') }} {{ $t('product.label', 2) }}
      </q-card-section>
      <q-card-section>
        <div class="row q-col-gutter-md items-center">
          <q-select
            class="col-4"
            use-input
            dense
            v-model="new_line_phase"
            input-debounce="0"
            @filter="filterOperations"
            :options="filtered_process"
            :label="$capitalize($t('phase.short'))"
            option-label="alias"
            popup-content-class="text-capitalize">
          </q-select>

          <q-select
            class="col-6"
            use-input
            dense
            v-model="new_line_product"
            @filter="filterProducts"
            :loading="catalog_loading"
            :options="filtered_products"
            :label="$capitalize($t('code') +' / '+ $t('description'))"
            option-label="code"
            input-class="text-capitalize">
            <template #option="scope">
              <q-item v-bind="scope.itemProps">
                <q-item-section>
                <q-item-label class="display">
                  {{ scope.opt.code }}
                </q-item-label>
                <q-item-label caption>
                  {{ scope.opt.description }}
                </q-item-label>
                </q-item-section>
              </q-item>
            </template>
          </q-select>

          <q-input
            dense
            class="col-2"
            v-model="new_line_qt"
            type="number"
            :label="$t('quantity.short')">
          </q-input>
        </div>
      </q-card-section>
      <div class="row q-col-gutter-md q-pa-md">
        <div class="col-6">
          <q-btn
            class="full-width"
            color="theme-blue"
            @click="addItem"
            :label="$t('add')">
          </q-btn>
        </div>
        <div class="col-6">
          <q-btn
            class="full-width"
            color="theme-grey"
            @click="show_product_catalog = false"
            :label="$t('cancel')">
          </q-btn>
        </div>
      </div>
    </q-card>
  </BaseDialog>
</template>

<script>
import { mapState, mapActions } from 'vuex'

import multiMatch from '@/lib/MultiFieldSearch.js'
import BaseDialog from '@/components/BaseDialog.vue'
import { api } from '@/boot/axios.js'
import { throttle as _throttle } from 'lodash'

export default {

  name: 'BillOfMaterials',

  components: {
    BaseDialog
  },

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
      show_cancel_confirmation: false,
      show_save_confirmation: false,
      saving: false,
      filtered_process: null,
      filtered_products: null
    };
  },

  computed: {
    ...mapState({
      // product_metadata: state => state.product.temp,
      saved_bom: state => state.bom.saved,
      saved_process: state => state.process.saved
    }),

    table_headers() {
    // TODO: refactor into mixin / composition function, used also in WorkSessionBom
      return [
        {
          name: 'component_code',
          field: 'component_code',
          label: this.$t('code').toUpperCase(),
          align: 'left'
        },
        {
          name: 'component_description',
          field: 'component_description',
          label: this.$t('description').toUpperCase(),
          align: 'left',
          style: 'width: 50%'
        },
        {
          name: 'phase_name',
          field: 'phase_name',
          label: this.$t('phase.short').toUpperCase(),
          align: 'left'
        },
        {
          name: 'qt',
          field: 'qt',
          label: this.$t('quantity.short').toUpperCase(),
        },
      ]
    },

    edit_mode: {
      get() {
        return this.$store.state.product.edit_modes.bom
      },
      set(value) {
        this.$store.commit('TOGGLE_EDIT_MODE', { view: 'bom', value })
      }
    },

    product_key() {
      return this.$route.params.product_key
    },

    product_metadata() {
      return this.$store.getters.productData(this.product_key)
    },

    temp_bom: {
      get() {
        return this.$store.state.bom.temp.map( i => { 
          return { ...i, table_key: i.component_key + i.phase_key }
        })
      },
      set(new_bom) {
        this.$store.commit('UPDATE_TEMP_BOM', new_bom)
      }
    },

    filtered_bom() {
      const fields_to_search = ['component_code', 'component_description', 'phase_name']
      return this.temp_bom.filter(line => {
        return multiMatch(this.search_text, line, fields_to_search)
      })
    },
  },

  methods: {
    ...mapActions(['loadProductDetails']),

    toggleEdit() {
      if (this.edit_mode == false) {
        this.edit_mode = true
      }
      else {
        this.edit_mode = false
        this.delete_lines = []
      }
    },

    toggleAll() {
      if (this.delete_lines.length) {
        this.delete_lines = []
      }
      else this.delete_lines = this.filtered_bom
    },

    openItemSearch() {
      this.catalog_loading = true
      this.show_product_catalog = true
      
      api.get('product').then( resp => {
        this.product_catalog = resp.data.filter(p => p._key != this.product_key)
      })
      this.catalog_loading = false
    },

    filterOperations(value, update) {
      if (value === '') {
        update(() => {
          this.filtered_process = [...this.saved_process]
        })
        return
      }
      update(() => {
        const needle = value.toLowerCase()
        this.filtered_process = this.saved_process.filter(o => {
          const include = o.alias.toLowerCase().includes(needle)
          return include
        })
      })
    },

    filterProducts(value, update) {
      if (value === '') {
        update(() => {
          this.filtered_products = [...this.product_catalog]
        })
        return
      }
      update(() => {
        const needle = value.toLowerCase()
        this.filtered_products = this.product_catalog.filter(p => {
          const include = multiMatch(needle, p, ['code', 'description'])
          return include
        })
      })
    },

    updateItemQt(table_key, qt) {
      let new_bom = [...this.temp_bom]
      new_bom.find( i => i.table_key === table_key).qt = qt
      this.$store.commit('UPDATE_TEMP_BOM', new_bom)
    },

    removeBomLines() {
      const lines_to_delete = this.delete_lines.map(l => l.table_key)
      const new_bom = this.temp_bom.filter( 
        line => !lines_to_delete.includes(line.table_key)
      )
      this.$store.commit('UPDATE_TEMP_BOM', new_bom)
      this.delete_lines = []
    },

    async addItem() {
      const is_duplicate = this.temp_bom.some(line => {
        return (
          line.component_key == this.new_line_product._key
          && line.phase_key == this.new_line_phase._key
        )
      })

      if (!is_duplicate) {
        
        const new_line = {
          /** 
           * Cannot simply add ...new_line because it would
           * contain an _id field that, when sent to the db would refer
           * to the relationship and raise an error.
           */ 
          component_key: this.new_line_product._key,
          component_code: this.new_line_product.code,
          component_description: this.new_line_product.description,
          qt: this.new_line_qt,
          phase_name: this.new_line_phase.alias,
          phase_key: this.new_line_phase._key,
          table_key: this.new_line_product._key + this.new_line_phase._key
        }

        this.temp_bom = [...this.temp_bom, new_line]
        this.show_product_catalog = false
      }
      else {
        window.alert(this.$capitalize(this.$t('bom.alerts.line_exists')))
      }
    },

    cancelChanges() {
      this.temp_bom = [...this.saved_bom]
      this.edit_mode = false
      this.delete_lines = []
      this.$emit('changes_canceled')

    },

    saveChanges() {
      this.saving = true
      const action_payload = {
        product_key: this.product_key,
        new_bom: this.temp_bom
      }
      this.$store.dispatch('saveBomChanges', action_payload)
      .then(() => {
        setTimeout(() => {
          this.saving = false
          this.edit_mode = false
          this.$emit('changes_saved')
        }, 1500)  
      })
      .catch( err => {
        if (err.response.status == 403) {
          const api_resp = err.response.data.detail
          const error_message = api_resp.message
                                + '\n\nLoops:\n'
                                + api_resp.data.join('\n')
          window.alert(error_message)
        }
        else {
          window.alert(err)
        }
        this.saving = false
      })
    },
  },

  mounted() {
    /* *
     * remove from container its padding and that of the column,
     * plus the footer height
     */ 
    this.filtered_process = [...this.saved_process]
    // const resizeTable = () => this.table_height = this.$refs.container.clientHeight - 24 - 52
    // resizeTable()
    // window.onresize = _throttle(resizeTable, 100)
  },

  watch: {
    // Reset form when closing/opening modal
    show_product_catalog() {
      this.new_line_product = null
      this.new_line_qt = null
      this.new_line_phase = null
    },
  }
};
</script>

<style lang="sass" scoped>
.my-sticky-header-table
  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-2)

  thead tr th
    position: sticky
    z-index: 1
    font-weight: bold !important
  /* this will be the loading indicator */
  thead tr:last-child th
    /* height of all previous header rows */
    top: 48px
  thead tr:first-child th
    top: 0

  thead tr th:last-child
    padding-right:38px

</style>
