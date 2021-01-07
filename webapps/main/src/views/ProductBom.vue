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
          v-model="search"
          class="ma-0 pa-0 align-center">
          <template v-slot:append>
            <span class="material-icons">{{ $tc('search') }}</span>
          </template>
        </v-text-field>

         <v-checkbox v-for="type in bom_types" :key="type" 
          :label="type" 
          v-model="item_type_filter" 
          :value="type"
          input-value="true"
          :color="$theme.blue">
        </v-checkbox>

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
       <v-col class="fill pa-0 pl-6" cols="9">          
        <v-data-table
          id="bom"
          :headers="table_headers"
          :items="filtered_bom"
          :show-select="edit_mode"
          v-model="delete_items"
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
                  v-if="edit_mode && delete_items.length"  
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
                  {{ $tc('bom.add_item') }}
                </v-btn>
              </v-col>  
            </v-row>  
          </template>
        </v-data-table>
      </v-col>  


    </v-row>

    <v-dialog
      v-model="show_item_catalog"
      max-width="600px"
      transition="dialog-transition"
      value="true" 
      :overlay-color="$theme.black"
      overlay-opacity=".9"
      no-click-animation>
      <v-card>
          <v-card-title class="display">
            {{ $tc('new') }} {{ $tc('item', 1) }}
          </v-card-title>
          <v-card-text>
            
          <v-row>
            <v-col cols="4">
              <v-autocomplete
                v-model="new_item_phase"
                :items="$store.state.process.saved"
                item-value="_key"
                item-text="alias"
                single-line
                return-object
                :label="$tc('phase.name', 1) | capitalize">
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
                v-model="new_item"
                :items="item_catalog"
                :loading="catalog_loading"
                item-value="_key"
                item-text="code"
                single-line
                return-object
                :label="$tc('code') +'/'+ $tc('description') | capitalize"
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
                v-model="new_item_qt"
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
      search: '',
      bom_types: ['assembly', 'component', 'consumable'],
      item_type_filter: ['assembly', 'component', 'consumable'],
      table_height: '85vh',
      delete_items: [],
      show_item_catalog: false,
      catalog_loading: false,
      item_catalog: [],
      new_item: {},
      new_item_phase: {},
      new_item_qt: null,
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
      return [
        {  value:'code', text: this.$tc('code').toUpperCase() },
        {  value:'description', text: this.$tc('description').toUpperCase() },
        {  value:'item_type', text: this.$tc('type').toUpperCase() },
        {  value:'phase_name', text: this.$tc('phase.name', 1).toUpperCase() },
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
      return this.temp_bom.filter(item => {
        let type_check = this.item_type_filter.includes(item.item_type.toLowerCase())

        return type_check && multiMatch(this.search, item, ['code', 'description'])
      })
    },

    deleteIconTooltip() {
      if (this.delete_items.length) {
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
        this.delete_items = []
      }
    },

    toggleAll() {
      if (this.delete_items.length) {
        this.delete_items = []
      }
      else this.delete_items = this.filtered_bom
    },

    openItemSearch() {
      this.catalog_loading = true
      this.show_item_catalog = true
      
      api.get('item').then( resp => {
        
        this.item_catalog = resp.data
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
        item => !this.delete_items.includes(item) 
      )
      this.$store.commit('UPDATE_TEMP_BOM', new_bom)
      this.delete_items = []
    },

    async addItem() {
      const is_duplicate = this.temp_bom.some(item => 
        item.code == this.new_item.code 
        && item.phase_key == this.new_item_phase._key
      )

      if (!is_duplicate) {
        
        const new_item = {
          /** 
           * Cannot simply add ...new_item because it would 
           * contain an _id field that, when sent to the db would refer
           * to the relationship and raise an error.
           */ 
          item_key: this.new_item._key,
          code: this.new_item.code,
          description: this.new_item.description,
          item_type: this.new_item.type,
          qt: this.new_item_qt,
          phase_name: this.new_item_phase.alias,
          phase_key: this.new_item_phase._key,
          table_key: this.new_item.code + this.new_item_phase._key
        }

        this.temp_bom = [...this.temp_bom, new_item]
        this.show_item_catalog = false
      }
      else {
        window.alert(c(this.$tc('bom.alerts.phase_item_exists')))
      }
    },

    cancelChanges() {
      this.temp_bom = [...this.saved_bom]
      this.edit_mode = false
      this.delete_items = []
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
    this.onresize
    const resizeTable = () => this.table_height = this.$refs.container.clientHeight - 24 - 52
    resizeTable()
    window.onresize = _throttle(resizeTable, 100)
  },

  watch: {
    // Reset form when closing/opening modal
    show_item_catalog() {
      this.new_item = null
      this.new_item_qt = null
      this.new_item_phase = null
    },
  }
};
</script>

<style lang="css" scoped>

</style>
