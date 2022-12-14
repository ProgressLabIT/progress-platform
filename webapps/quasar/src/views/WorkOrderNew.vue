<template>
  <BaseModalForm
    id="new-work-order-form"
    @submit="postNewWorkOrder"
    max_width="700px"
    @cancel="$router.back()">

    <template v-slot:title>
      {{ $t('work_order.new') }}
    </template>
    
    <template v-slot:form>
      <div class="weight-bold text-uppercase text-low">
        {{ $t('work_order.wo_code') }}
      </div>

      <!-- WORK ORDER CODE INPUT -->
      <q-input v-model="wo_code" />

      <!-- WORK ORDER LINES TITLE  -->
      <div class="text-h4 weight-bold text-uppercase">
        {{ $t('work_order.wo_line.short', 2) }}
      </div>

      <!-- WORK ORDER LINE HEADERS -->
      <div class="row">
        <div
          v-for="(info, field_name) in wo_line_info"
          :key="field_name"
          :class="`q-pb-none col-${info.cols}`">
          <span>{{ $capitalize(info.label) }}</span>
        </div>
      </div>

      <!-- WORK ORDER LINES -->
      <div class="row" v-for="(line, index) in wo_lines" :key="index">
        <div
          v-for="(info, field_name) in wo_line_info" 
          :key="field_name"
          :cols="info.cols"
          class="q-py-none">
          
          <q-dialog
            :value="show_picker === index" 
            @input="log($event)"
            @click:outside="show_picker = -1"
            @keydown.esc="show_picker = -1"
            width="300px"
            v-if="field_name === 'due_by'">
            <q-date
              minimal
              width="300px"
              @change="setDueBy($event, index)">
            </q-date>
          </q-dialog>

          <q-input
            readonly              
            v-if="field_name === 'due_by'"
            @click.stop="show_picker = index"
            :value="wo_lines[index].due_by">
          </q-input>

          <q-select
            v-else-if="field_name === 'product'"
            :options="product_list"
            option-label="code"
            v-model="wo_lines[index].product">
          </q-select>

          <q-select
            v-else
            autocomplete="false"
            :input-class="{ 'text-right': info.type === Number }"
            :type="field_name === 'qt_planned' ? 'number' : '' "
            v-model="wo_lines[index][field_name]">
          </q-select>
        
        </div>

        <div class="col-1">
          <q-icon v-if="index != 0" @click="deleteRow(index)" name="mdi-close" />
        </div>
      </div>

      <q-btn flat class="display medium" @click="addLine">
        + {{ $t('work_order.add_line', 1) }}
      </q-btn>

    </template>

    <template v-slot:actions>
      <q-btn
        class="col-6"
        color="theme-blue"
        :loading="loading"
        @click="postNewWorkOrder">
        {{ $t('save') }}
      </q-btn>
      <q-btn
        class="col-6"
        color="theme-grey"
        @click="$router.back()">
        {{ $t('cancel') }}
      </q-btn>
    </template>

  </BaseModalForm>

</template>

<script>
import BaseModalForm from '@/components/BaseModalForm.vue'

export default {

  name: 'WorkOrderNew',

  components: {
    BaseModalForm
  },

  data () {
    return {
      wo_code: null,
      wo_lines: [],
      show_picker: -1,
      loading: false,

    }
  },

  computed: {
    wo_line_info() {
      return {
        product: {
          label: this.$t('product.label'),
          type: Object,
          cols: 5,
          initial_value: {}
        },
        qt_planned: {
          label: this.$t('quantity.long'),
          type: Number,
          cols: 3,
          initial_value: 0
        },
        due_by: {
          label: this.$t('by'),
          type: Date,
          cols: 3,
          initial_value: ''
        }
      }
    },

    product_list() {
      return this.vuex_ready
        ? this.$store.getters.productCatalog()
        : []
    }
  },

  methods: {
    addLine() {
      let empty_line = Object.fromEntries(
        Object.entries(this.wo_line_info).map( ([field, value]) => [field, value.initial_value] )
      )
      this.wo_lines.push(empty_line)
      // this.wo_lines ++
    },

    postNewWorkOrder() {
      const wo_code_missing = !this.wo_code
      const quantity_missing = this.wo_lines.some( line => line.qt_planned == 0 )
      const product_missing = this.wo_lines.some( line => !line.product._key )

      if (wo_code_missing || quantity_missing || product_missing)  {
        window.alert(capitalize(this.$t('form_missing_fields_alert')))

      }

      else {
        let new_records = this.wo_lines.map( (line, index) => {
        return {
          wo_code: this.wo_code.toUpperCase(),
          wo_line: index + 1,
          product_key: line.product._key,
          product_code: line.product.code,
          product_description: line.product.description,
          qt_planned: line.qt_planned,
          due_by: line.due_by
          }
        })
        this.loading = true
        this.$store.dispatch('postWorkOrder', new_records)
        .then( () => {
          this.wo_lines = []
          this.loading = false
          this.$router.back()
        })
        .catch( err => {
          window.alert(err)
          this.loading = false
        })
      }
    },

    setDueBy(date, line) {
      this.$set(this.wo_lines[line], 'due_by', date)
      this.show_picker = -1
    },

    deleteRow(index) {
      this.wo_lines.splice(index,1)
    }
  },

  created() {
    this.$store.dispatch('loadProductList')
    let today = new Date()
    this.wo_line_info.due_by.initial_value =  '' 
      + today.getFullYear()
      + '-'
      + (today.getMonth() + 1)
      + '-'
      + today.getDate()
    this.addLine()
  }
}
</script>

<style lang="sass">
#new-work-order-form .q-dialog__backdrop
  background-color: v-bind('$theme.background')
</style>
