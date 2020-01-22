<template>
  <v-container fill-height fluid>    
    <v-row class="mx-0 fill" align="start">
      <!-- <v-col cols="3" style="position:fixed"> -->
      <v-col cols="3" class="d-flex flex-column fill align-content-end">

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
          dense 
          :label="type" 
          v-model="item_type_filter" 
          :value="type"
          input-value="true"
          :color="$theme.blue">
        </v-checkbox>

        <v-spacer></v-spacer>

        <v-btn class="mt-6" :color="$theme.blue">MODIFICA DISTINTA</v-btn>

      </v-col>  
  
       <!-- <v-col class="fill" cols="9" offset="3"> -->
       <v-col class="fill" cols="9">

        <v-card outlined class="fill scroll">
          
        <v-data-table
          :headers="bom_headers"
          :items="filtered_bom"
          fixed-header  
          item-key="code"
          disable-pagination
          hide-default-footer
        >
          <template v-slot:footer>
            <v-divider></v-divider>
            <v-row justify="center" align="center">
              <v-col cols="auto" class="smaller">
                SHOWING {{ filtered_bom.length }} of {{ bom.length }} ITEMS
              </v-col>
            </v-row>  
          </template>
        </v-data-table>
        </v-card>
      </v-col>  


    </v-row>
  </v-container>
</template>

<script>
import { mapState, mapActions } from 'vuex'
// import ProductAside from '@/components/ProductAside.vue'

export default {

  name: 'BillOfMaterials',

  props: ['item_key'],

  // components: {
  //   ProductAside
  // },

  data() {
    return {
      search: '',
      bom_types: ['assembly', 'material', 'consumable'],
      item_type_filter: ['assembly', 'material', 'consumable'],
    };
  },

  computed: {
    ...mapState({
      product_metadata: state => state.current_product.metadata, 
      bom: state => state.current_product.bom
    }),

    filtered_bom() {
      return this.bom.filter(item => {
        let type_check = this.item_type_filter.includes(item.type.toLowerCase())
        let search_context = (item.code + ' ' + item.description).toLowerCase()
        let search_match = this.search.length ? search_context.includes(this.search.toLowerCase()) : true

        return type_check && search_match
      })
    },

    bom_headers() {
      let headers = []
      Object.keys(this.bom[0]).forEach(header => {
        headers.push({ text: header, value: header })
      })
      return headers
    },
  },

  methods: {
    ...mapActions(['loadProductDetails'])
  },

  created() {
    this.loadProductDetails(this.item_key)
  }
};
</script>

<style lang="css" scoped>

</style>
