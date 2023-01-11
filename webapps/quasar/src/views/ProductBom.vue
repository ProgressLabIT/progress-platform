<template>
  TEST
</template>

<script>
import { mapState, mapActions } from 'vuex'

import multiMatch from '@/lib/MultiFieldSearch.js'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import { api } from '@/boot/axios.js'
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
        {  value:'product_code', text: this.$t('code').toUpperCase() },
        {  value:'product_description', text: this.$t('description').toUpperCase() },
        {  value:'phase_name', text: this.$t('phase.short').toUpperCase() },
        {  value:'qt', text: this.$t('quantity.short').toUpperCase() },
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
        return this.$t('deselect_all')
      }
      else return this.$t('select_all')
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
        window.alert(this.$capitalize(this.$t('bom.alerts.line_exists')))
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
