<template>
   <v-data-table
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
    :height="table_height"
  >
    <template v-slot:item.code="{item}">
      <div class="nowrap">{{ item.code }}</div>
    </template>
  </v-data-table>
</template>

<script>
export default {

  name: 'WorkSessionBom',

  computed: {
   table_headers() {
   // TODO: refactor into mixin / composition function, used also in ProductBoM
      return [
        {  value:'code', text: this.$tc('code').toUpperCase() },
        {  value:'description', text: this.$tc('description').toUpperCase() },
        {  value:'item_type', text: this.$tc('type').toUpperCase() },
        {  value:'phase_name', text: this.$tc('phase.name', 1).toUpperCase() },
        {  value:'qt', text: this.$tc('quantity.short').toUpperCase() },
      ]
    },

    bom () {
      const job_data = this.$store.state.traceability.working_job_data
      return job_data.phase_bom.map(i => {
        // multiply items by job quantity. Does not apply to tools and safety items
        const multiply = ['assembly', 'component', 'consumable']
        if (multiply.includes(i.item_type)) {
          i.qt = i.qt * job_data.qt_planned
        }
        return i
      })
    }
  }
}
</script>

<style lang="css" scoped>
</style>
