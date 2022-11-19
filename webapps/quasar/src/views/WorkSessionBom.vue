<template>
  <div class="absolute-full column">

    <NoDataAlert v-if="!bom.length">
      {{ $t('bom.missing') }}
    </NoDataAlert>

    <template v-else>
      <q-table
        id="bom"
        class="my-sticky-header-table col"
        card-class="surface1 shadow-0"
        virtual-scroll
        :rows="bom"
        :columns="columns"
        style="height: 100%"
        :pagination="{ rowsPerPage: 0 }"
        :rows-per-page-options="[0]"
        hide-bottom>
      </q-table>

      <div class="row items-center justify-center col-auto q-px-md text-body2">
        <span class="q-mr-3">
          {{ $capitalize($t('bom.quantity_type.radio_label')) }}
        </span>
        <q-radio
          v-for="type in qt_types"
          v-model="quantity_type"
          :key="type"
          :val="type"
          :label="$t('bom.quantity_type.' + type).toUpperCase()">
        </q-radio>
      </div>
    </template>

  </div>
</template>

<script>
import BaseModalForm from '@/components/BaseModalForm.vue'
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
    BaseModalForm,
    NoDataAlert
  },

  data () {
    return {
      quantity_type: 'job',
      qt_types: ['job', 'batch'],
      show_lot_input: false,
    }
  },

  computed: {
    columns() {
    // TODO: refactor into mixin / composition function, used also in ProductBoM
      return [
        {  name:'code', field: 'product_code', label: this.$t('code').toUpperCase(), align: 'left' },
        {  name:'description', field: 'product_description', label: this.$t('description').toUpperCase(), align: 'left' },
        {  name:'item_type', field: 'item_type', label: this.$t('type').toUpperCase(), align: 'left' },
        {  name:'phase_name', field: 'phase_name', label: this.$t('phase.short', 1).toUpperCase(), align: 'left' },
        {  name:'qt', field: 'qt', label: this.$t('quantity.short').toUpperCase() },
      ]
    },

    bom () {
      const base_bom = this.job.hasOwnProperty('job_bom')
        ? this.job.job_bom.map(i => {
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
        return Array(100).fill(base_bom[0])
    }
  }
}
</script>

<style lang="sass" scoped>
.my-sticky-header-table
  thead tr th
    position: sticky
    z-index: 1
  thead tr:first-child th
    top: 0
</style>
