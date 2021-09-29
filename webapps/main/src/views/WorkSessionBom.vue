<template>
  <v-container class="fill pa-0">

    <NoDataAlert v-if="!bom.length">{{ $tc('bom.missing') }}</NoDataAlert>

    <v-row v-else class="fill-height ma-0 pa-0">
      <v-col class="fill-heigh d-flex flex-column justify-space-between pa-0">
        <v-data-table
          id="bom"
          :headers="table_headers"
          :items="bom"
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

        <v-radio-group row v-model="quantity_type" hide-details class="pa-4">
          <v-row class="pa-0 ma-0">
            <span class="mr-3">{{ $tc('bom.quantity_type.radio_label') | capitalize }}</span>
            <v-radio
              v-for="type in qt_types"
              :key="type"
              :value="type">
              <template v-slot:label>
                <span class="body-2">{{ $tc('bom.quantity_type.' + type).toUpperCase() }}</span>
              </template>
            </v-radio>
          </v-row>
        </v-radio-group>
      </v-col>

      <v-btn
        absolute rounded
        bottom right
        :color="$theme.blue"
        @click="show_lot_input = true">
        REGISTRA LOTTI MATERIALI
      </v-btn>

      <BaseModalForm :show="show_lot_input" @cancel="show_lot_input = false">
        <template v-slot:title>
          REGISTRAZIONE LOTTI MATERIALI
        </template>

        <template v-slot:form>
          <v-container>
            <v-row v-for="item in components" :key="item" align="center">
              <v-col cols="4">{{ item }}</v-col>
              <v-col cols="6" offset="2">
                <v-autocomplete :items="lots">
                </v-autocomplete>
              </v-col>
            </v-row>
          </v-container>
        </template>
      </BaseModalForm>


    </v-row>

  </v-container>
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
      components: [
        'M010102',
        'M020237',
        'M030111',
        'M020305'
      ],
      lots: [
        'INTRAUE',
        'EXTRAUE'
      ]
    }
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
