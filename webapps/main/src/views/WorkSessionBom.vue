<template>
  <div class="absolute-full column">

    <NoDataAlert v-if="!bom.length">
      {{ $t('bom.missing') }}
    </NoDataAlert>

    <template v-else>
      <q-table
        id="bom"
        ref="bom"
        class="my-sticky-header-table col"
        card-class="surface1 shadow-0"
        virtual-scroll
        :rows="bom"
        :columns="columns"
        :pagination="{ rowsPerPage: 0 }"
        :rows-per-page-options="[0]"
        :virtual-scroll-sticky-size-start="48"
        hide-bottom>
      </q-table>

      <q-separator />

      <div class="row items-center col-auto q-px-md text-body2">
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
        <q-space />
        <q-btn size="sm" color="theme-blue" @click="$refs.bom.scrollTo(0)">
          {{ $t('scroll.to_top') }}
        </q-btn>
      </div>

      <!-- INSERT HERE DIALOG FOR COMPONENT LOT REGISTRATION -->
      <!-- <BaseModalForm :show="show_lot_input" @cancel="show_lot_input = false">
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
      </BaseModalForm> -->
    </template>

  </div>
</template>

<script>
// import BaseModalForm from '@/components/BaseModalForm.vue'
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
  //  BaseModalForm,
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
        {  name:'code', field: 'component_code', label: this.$t('code').toUpperCase(), align: 'left' },
        {  name:'description', field: 'component_description', label: this.$t('description').toUpperCase(), align: 'left' },
        {  name:'item_type', field: 'item_type', label: this.$t('type').toUpperCase(), align: 'left' },
        {  name:'phase_name', field: 'phase_name', label: this.$t('phase.short', 1).toUpperCase(), align: 'left' },
        {  name:'qt', field: 'qt', label: this.$t('quantity.short').toUpperCase() },
      ]
    },

    bom () {
      return this.job.hasOwnProperty('job_bom')
        ? this.job.job_bom.map(i => {
          // multiply items by job quantity. Does not apply to tools and safety items
          let quantity = i.qt
          const factor = this.quantity_type === 'job' ? this.job.qt_planned : this.job.parameters.production_batch_qt
          quantity = i.qt * factor
          return {
            ...i,
            qt: quantity
          }
        }) : []
    }
  }
}
</script>

<style lang="sass" scoped>
.my-sticky-header-table
  height: 400px

  .q-table__top,
  .q-table__bottom,
  thead tr:first-child th /* bg color is important for th; just specify one */
    background-color: var(--surface-1)

  thead tr th
    position: sticky
    z-index: 1
  /* this will be the loading indicator */
  thead tr:last-child th
    /* height of all previous header rows */
    top: 48px
  thead tr:first-child th
    top: 0
</style>
