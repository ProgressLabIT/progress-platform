<template>
  <v-container fill-height fluid ref="container">    
    <v-row class="mx-0 fill" align="start">
      <!-- <v-col cols="3" style="position:fixed"> -->
      <v-col cols="3" class="d-flex flex-column fill align-content-end pt-1">

        <h1 class="display highlight mb-2">{{ product_metadata.code }}</h1>
        <p>{{ product_metadata.description }}</p>
        
        <h5 class="mt-12">FILTRI</h5>

        <v-text-field
          hide-details
          single-line
          autocomplete="false"
          name="search"
          label="Codice o Descrizione"
          v-model="search"
          class="ma-0 pa-0 align-center">
          <template v-slot:append>
            <span class="material-icons">search</span>
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
          :color="edit_table ? $theme.green : $theme.blue"
          @click="toggleEdit"
          >
          {{ edit_table ? 'SALVA DISTINTA' : 'MODIFICA DISTINTA' }}
        </v-btn>

      </v-col>  
  
      <!-- BOM DATA -->
       <v-col class="fill pa-0 pl-6" cols="9">          
        <v-data-table
          id="bom"
          :headers="bom_headers"
          :items="filtered_bom"
          :show-select="edit_table"
          v-model="delete_items"
          loading-text="Recupero dati in corso..."
          sort-by="code"
          fixed-header  
          item-key="code"
          disable-pagination
          hide-default-footer
          :height="table_height"
        >
          <template v-slot:item.code="{item}">
            <div class="nowrap">{{ item.code }}</div>
          </template>

          <template v-slot:item.qt="{item}" v-if="edit_table">
            <v-text-field
              hide-details dense
              type="number"
              min="0"
              v-model="item.qt"
              style="width:70px"
            ></v-text-field>            
          </template>

          <template v-slot:header.data-table-select="">
            <TooltipIcon small 
              :color="$theme.red" 
              icon="delete"
              :tooltip="deleteIconTooltip"
              @iconClick="toggleAll"
              class="mx-n1">
            </TooltipIcon>
          </template>
          
          <template v-slot:item.data-table-select="{ isSelected, select }">
            <v-simple-checkbox :color="$theme.red" :value="isSelected" @input="select($event)"></v-simple-checkbox>
          </template>
          
          <template v-slot:footer>
            <v-divider></v-divider>
            <v-row align="center" class="mx-0" style="height: 52px">

              <v-col cols="4">
                <v-btn v-if="edit_table && delete_items.length" small :color="$theme.red">
                  <v-icon small>delete</v-icon>elimina selezionati</v-btn>
              </v-col>  
              
              <v-col cols="4" class="smaller text-center">
                {{ filtered_bom.length }} di {{ bom.length }} ELEMENTI
              </v-col>
              
              <v-col cols="4" class="d-flex justify-end" >
                <v-btn small 
                  v-if="edit_table" 
                  :color="$theme.blue"
                  @click="openItemSearch">
                  <v-icon small class="mr-2 pl-0">add</v-icon>
                  aggiungi articolo
                </v-btn>
              </v-col>  
            </v-row>  
          </template>
        </v-data-table>
      </v-col>  


    </v-row>

    <v-dialog
      v-model="show_item_catalog"
      max-width="500px"
      transition="dialog-transition"
      value="true" 
      :overlay-color="$theme.black"
      overlay-opacity=".9"
      no-click-animation>
      <v-card>
          <v-card-title class="display">
            Nuovo articolo
          </v-card-title>
          <v-card-text>
            
          <v-row>
            <v-col cols="9">
              <v-autocomplete
                v-model="new_item"
                :items="item_catalog"
                :loading="catalog_loading"
                item-value="_key"
                item-text="code"
                single-line
                return-object
                label="Inserisci codice o descrizione"
              >
                <template v-slot:item="data">
                  <v-list-item-content>
                    <v-list-item-title class="display" v-html="data.item.code"></v-list-item-title>
                    <v-list-item-subtitle v-html="data.item.description"></v-list-item-subtitle>
                  </v-list-item-content>
                </template>

                <template v-slot:selection="data">
                  {{ data.item.code }}
                </template>

              </v-autocomplete>
              
            </v-col>  
            <v-col cols="3">
              <v-text-field
                type="number" min="0"
                label="qt"
                v-model="new_item_qt"
                single-line
              ></v-text-field>
            </v-col>  
          </v-row>  
          </v-card-text>
          <v-card-actions class="px-4">
            <v-btn block 
              :color="$theme.blue"
              @click="addItem">aggiungi</v-btn>
          </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import multiMatch from '@/lib/MultiFieldSearch.js'
import TooltipIcon from '@/components/TooltipIcon'
import { api } from '@/lib/apiCall.js'

export default {

  name: 'BillOfMaterials',

  components: {
    TooltipIcon
  },

  data() {
    return {
      search: '',
      bom_types: ['assembly', 'component', 'consumable'],
      item_type_filter: ['assembly', 'component', 'consumable'],
      table_height: '85vh',
      edit_table: false,
      delete_items: [],
      show_item_catalog: false,
      catalog_loading: false,
      item_catalog: [],
      new_item: {},
      new_item_qt: null,
    };
  },

  computed: {
    ...mapState({
      product_metadata: state => state.product.details, 
      bom: state => state.bom.items
    }),

    product_key() {
      return this.$route.params.item_key
    },

    filtered_bom() {
      return this.bom.filter(item => {
        let type_check = this.item_type_filter.includes(item.type.toLowerCase())

        return type_check && multiMatch(this.search, item, ['code', 'description'])
      })
    },

    bom_headers() {
      let headers = []
      Object.keys(this.bom[0]).forEach(header => {
        // exclude fields not necessary in the table
        if (['_key', 'rel_id', 'operation', 'phase_key', 'phase_seq'].includes(header)) return 

        let header_params = { text: header, value: header }
        headers.push(header_params)
      })
      return headers
    },

    deleteIconTooltip() {
      if (this.delete_items.length) {
        return 'Deseleziona tutti'
      }
      else return 'Seleziona tutti'
    }
  },

  methods: {
    ...mapActions(['loadProductDetails', 'getItemsCatalog']),

    toggleEdit() {
      if (this.edit_table == false) {
        this.edit_table = true
      }
      else {
        this.edit_table = false
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

    addItem() {
      const new_item = {
        ...this.new_item,
        qt: this.new_item_qt,
        rel_id: ''
      }
      console.log({new_item})
      let new_bom = this.bom
      new_bom.push(new_item)
      this.$store.commit('UPDATE_BOM', new_bom)
      this.new_item = null
      this.new_item_qt = null
      this.show_item_catalog = false
    }
  },

  created() {
    this.loadProductDetails(this.product_key)
  },

  mounted() {
    /* *
     * remove from container its padding and that of the column,
     * plus the footer height
     */ 
    this.table_height = this.$refs.container.clientHeight - 24 - 52
  }
};
</script>

<style lang="css" scoped>

</style>
