<template>
  <v-container fill-height fluid ref="container">    
    <v-row class="mx-0 fill" align="start">
      <!-- <v-col cols="3" style="position:fixed"> -->
      <v-col cols="3" class="d-flex flex-column fill align-content-end pt-1">

        <h1 class="display highlight mb-2">{{ product_metadata.code }}</h1>
        <p>{{ product_metadata.description }}</p>
        
        <h5 class="mt-12 text-uppercase">{{ $tc('filters') }}</h5>

        <v-text-field
          hide-details
          single-line
          autocomplete="off"
          name="search"
          label="Codice o Descrizione"
          v-model="search_text"
          class="ma-0 pa-0 align-center">
          <template v-slot:append>
            <span class="material-icons">{{ $tc('search') }}</span>
          </template>
        </v-text-field>

        <v-spacer></v-spacer>

        <v-btn 
          class="mt-auto" 
          v-if="!edit_mode"
          @click="toggleEdit"
          :color="$theme.blue"
          >
          {{ $tc('bom.edit') }}
        </v-btn>

        <div v-else>
          <v-btn block class="mb-2" 
            :color="$theme.green" 
            @click="saveChanges"
            :loading="saving">
            {{ $tc('save') }}
          </v-btn>

          <v-btn block 
            :disabled="saving" 
            :color="$theme.grey" 
            @click="cancelChanges">
            {{ $tc('cancel') }}
          </v-btn>
        </div>  

        <!-- CANCEL CONFIRMATION -->
        <v-snackbar
          top :timeout="2000"
          :color="$theme.grey"
          v-model="show_cancel_confirmation">
          {{ $tc('snackbars.changes_canceled') | capitalize }}
          <v-btn text @click.native="show_cancel_confirmation = false">OK</v-btn>
        </v-snackbar>

        <!-- SAVE NOTIFICATION -->
        <v-snackbar
          top :timeout="2000"
          :color="$theme.green"
          v-model="show_save_confirmation"
          class="text-uppercase">
          {{ $tc('bom.updated') }}
          <v-btn text :color="$theme.white" @click.native="show_save_confirmation = false">
            <v-icon>close</v-icon>
          </v-btn>
        </v-snackbar>

      </v-col>  
  
      <!-- BOM DATA -->
       <v-col class="pa-0 pl-6" cols="9">
       <v-card>
        <v-data-table
          id="bom"
          :headers="table_headers"
          :items="filtered_bom"
          :show-select="edit_mode"
          v-model="delete_lines"
          :loading-text="$tc('loading_text') | capitalize"
          sort-by="code"
          fixed-header  
          item-key="table_key"
          disable-pagination
          hide-default-footer
          :height="table_height"
        >
          <template v-slot:item.code="{item}">
            <div class="nowrap">{{ item.code }}</div>
          </template>

          <template v-slot:item.qt="{item}" v-if="edit_mode">
            <v-text-field
              hide-details dense
              type="number"
              min="0"
              :value="item.qt"
              @blur="updateItemQt(item.table_key, $event.target.value)"
              style="width:70px"
            ></v-text-field>            
          </template>

          <template v-slot:header.data-table-select="">
            <BaseTooltipIcon small 
              :color="$theme.red" 
              icon="delete"
              :tooltip="deleteIconTooltip | capitalize"
              @iconClick="toggleAll"
              class="mx-n1">
            </BaseTooltipIcon>
          </template>
          
          <template v-slot:item.data-table-select="{ isSelected, select }">
            <v-simple-checkbox :color="$theme.red" :value="isSelected" @input="select($event)"></v-simple-checkbox>
          </template>
          
          <template v-slot:footer>
            <v-divider></v-divider>
            <v-row align="center" class="mx-0" style="height: 52px">

              <v-col cols="4">
                <v-btn small
                  v-if="edit_mode && delete_lines.length"
                  :color="$theme.red"
                  @click="removeSelectedItems">
                  <v-icon small>delete</v-icon>
                  {{ $tc('bom.delete_selected') }}
                </v-btn>
              </v-col>  
              
              <v-col cols="4" class="smaller text-center">
                {{ filtered_bom.length }} {{ $tc('of') }} {{ temp_bom.length }} {{ $tc('element', 2).toUpperCase() }}
              </v-col>
              
              <v-col cols="4" class="d-flex justify-end" >
                <v-btn small 
                  v-if="edit_mode" 
                  :color="$theme.blue"
                  @click="openItemSearch">
                  <v-icon small class="mr-2 pl-0">add</v-icon>
                  {{ $tc('bom.add_line') }}
                </v-btn>
              </v-col>  
            </v-row>  
          </template>
        </v-data-table>
        </v-card>
      </v-col>  


    </v-row>

    <v-dialog
      v-model="show_product_catalog"
      max-width="600px"
      transition="dialog-transition"
      value="true" 
      :overlay-color="$theme.background"
      overlay-opacity=".9"
      no-click-animation>
      <v-card>
          <v-card-title class="display">
            {{ $tc('new') }} {{ $tc('product', 1) }}
          </v-card-title>
          <v-card-text>
            
          <v-row>
            <v-col cols="4">
              <v-autocomplete
                v-model="new_line_phase"
                :items="$store.state.process.saved"
                item-value="_key"
                item-text="alias"
                single-line
                return-object
                :label="$tc('phase.short') | capitalize">
                <template v-slot:selection="data">
                  {{ data.item.alias | capitalize }}
                </template>
                <template v-slot:item="data">
                  <v-list-item-content>
                    <v-list-item-title>{{ data.item.alias | capitalize }}</v-list-item-title>
                  </v-list-item-content>
                </template>
              </v-autocomplete>
            </v-col>  
            <v-col cols="6">
              <v-autocomplete
                v-model="new_line"
                :items="product_catalog"
                :loading="catalog_loading"
                item-value="_key"
                item-text="code"
                single-line
                return-object
                :label="$tc('code') +' / '+ $tc('description') | capitalize"
              >
                <template v-slot:item="data">
                  <v-list-item-content>
                    <v-list-item-title class="display">{{ data.item.code }}</v-list-item-title>
                    <v-list-item-subtitle>{{ data.item.description }}</v-list-item-subtitle>
                  </v-list-item-content>
                </template>

                <template v-slot:selection="data">
                  {{ data.item.code }}
                </template>

              </v-autocomplete>
              
            </v-col>  
            <v-col>
              <v-text-field
                type="number" min="0"
                :label="$tc('quantity.short')"
                v-model="new_line_qt"
                single-line
              ></v-text-field>
            </v-col>  
          </v-row>  
          </v-card-text>
          <v-card-actions class="px-4">
            <v-btn block 
              :color="$theme.blue"
              @click="addItem">{{ $tc('add') }}</v-btn>
          </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapState, mapActions } from 'vuex'

import { capitalize as c } from '@/lib/filters.js'
import multiMatch from '@/lib/MultiFieldSearch.js'
import BaseTooltipIcon from '@/components/BaseTooltipIcon'
import { api } from '@/lib/apiCall.js'
import { throttle as _throttle } from 'lodash'

export default {

  name: 'BillOfMaterials',

  components: {
    BaseTooltipIcon
  },

  data() {
    return {
      search_text: '',
      table_height: '83vh',
      delete_lines: [],
      show_product_catalog: false,
      catalog_loading: false,
      product_catalog: [],
      new_line: {},
      new_line_phase: {},
      new_line_qt: null,
      show_cancel_confirmation: false,
      show_save_confirmation: false,
      saving: false,
    };
  },

  computed: {
    ...mapState({
      // product_metadata: state => state.product.temp,
      saved_bom: state => state.bom.saved
    }),

    table_headers() {
    // TODO: refactor into mixin / composition function, used also in WorkSessionBom
      return [
        {  value:'product_code', text: this.$tc('code').toUpperCase() },
        {  value:'product_description', text: this.$tc('description').toUpperCase() },
        {  value:'phase_name', text: this.$tc('phase.short').toUpperCase() },
        {  value:'qt', text: this.$tc('quantity.short').toUpperCase() },
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
          return { ...i, table_key: i.code + i.phase_key }
        })
      },
      set(new_bom) {
        this.$store.commit('UPDATE_TEMP_BOM', new_bom)
      }
    },

    filtered_bom() {
      return this.temp_bom.filter(line => {
        return multiMatch(this.search_text, line, ['code', 'description'])
      })
    },

    deleteIconTooltip() {
      if (this.delete_lines.length) {
        return this.$tc('deselect_all')
      }
      else return this.$tc('select_all')
    }
  },

  methods: {
    ...mapActions(['loadProductDetails', 'getItemsCatalog']),

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

    updateItemQt(table_key, qt) {
      let new_bom = [...this.temp_bom]
      new_bom.find( i => i.table_key === table_key).qt = qt
      this.$store.commit('UPDATE_TEMP_BOM', new_bom)
    },

    removeSelectedItems() {
      const new_bom = this.temp_bom.filter( 
        line => !this.delete_lines.includes(line)
      )
      this.$store.commit('UPDATE_TEMP_BOM', new_bom)
      this.delete_lines = []
    },

    async addItem() {
      const is_duplicate = this.temp_bom.some(line =>
        line.code == this.new_line.code
        && line.phase_key == this.new_line_phase._key
      )

      if (!is_duplicate) {
        
        const new_line = {
          /** 
           * Cannot simply add ...new_line because it would
           * contain an _id field that, when sent to the db would refer
           * to the relationship and raise an error.
           */ 
          product_key: this.new_line._key,
          product_code: this.new_line.code,
          product_description: this.new_line.description,
          qt: this.new_line_qt,
          phase_name: this.new_line_phase.alias,
          phase_key: this.new_line_phase._key,
          table_key: this.new_line.code + this.new_line_phase._key
        }

        this.temp_bom = [...this.temp_bom, new_line]
        this.show_product_catalog = false
      }
      else {
        window.alert(c(this.$tc('bom.alerts.line_exists')))
      }
    },

    cancelChanges() {
      this.temp_bom = [...this.saved_bom]
      this.edit_mode = false
      this.delete_lines = []
      this.show_cancel_confirmation = true
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
          this.show_save_confirmation = true
          this.saving = false
          this.edit_mode = false
        }, 1500)  
      })
      .catch( err => {
        window.alert(err)
        this.saving = false
      })
    },
  },

  mounted() {
    /* *
     * remove from container its padding and that of the column,
     * plus the footer height
     */ 
    const resizeTable = () => this.table_height = this.$refs.container.clientHeight - 24 - 52
    resizeTable()
    window.onresize = _throttle(resizeTable, 100)
  },

  watch: {
    // Reset form when closing/opening modal
    show_product_catalog() {
      this.new_line = null
      this.new_line_qt = null
      this.new_line_phase = null
    },
  }
};
</script>

<style lang="css" scoped>

</style>
