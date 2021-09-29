<template>
  <v-container class="fill">

     <v-data-table v-if="bom.length"
      id="bom"
      :headers="table_headers"
      :items="bom"
      v-model="delete_items"
      :loading-text="$tc('loading_text') | capitalize"
      sort-by="code"
      fixed-header
      item-key="table_key"
      disable-pagination
      hide-default-footer
      :height="table_height">
      <template v-slot:item.code="{item}">
        <div class="nowrap">{{ item.code }}</div>
      </template>
    </v-data-table>

    <NoDataAlert v-else>{{ $tc('bom.missing') }}</NoDataAlert>

  </v-container>
</template>

<script>
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {

  name: 'WorkSessionBom',

  props: {
    job: {
      type: Object,
      required: true
    }
  },

  components: {
    NoDataAlert
  },

  computed: {
    table_headers() {
    // TODO: refactor into mixin / composition function, used also in ProductBoM
      return [
        {  value:'code', text: this.$tc('code').toUpperCase() },
        {  value:'description', text: this.$tc('description').toUpperCase() },
        {  value:'item_type', text: this.$tc('type').toUpperCase() },
        {  value:'phase_name', text: this.$tc('phase.short', 1).toUpperCase() },
        {  value:'qt', text: this.$tc('quantity.short').toUpperCase() },
      ]
    },

    bom () {
      return this.job.hasOwnProperty('phase_bom')
        ? this.job.phase_bom.map(i => {
          // multiply items by job quantity. Does not apply to tools and safety items
          const multiply = ['assembly', 'component', 'consumable']
          let quantity = i.qt
          if (multiply.includes(i.item_type)) {
            const factor = this.quantity_type === 'job' ? this.job.qt_planned : this.job.parameters.production_batch_qt
            quantity = i.qt * factor
          }
          return {
            ...i,
            qt: quantity
          }
        }) : []
    }
  }
}
</script>

<style lang="css" scoped>
</style>
