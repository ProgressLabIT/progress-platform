<template>
  <BaseModalForm @submit="postNewWorkOrder" max_width="70vw" @cancel="$router.back()">
    <template v-slot:title>
      {{ $tc('work_order.new') }}
    </template>
    
    <template v-slot:form>

      <!-- WORK ORDER DATA HEADERS -->
      <v-row>
        <v-col 
          v-for="(info, field_name) in new_wo_info"
          :key="field_name"
          :cols="info.cols"
          class="pb-0">
          <span>{{ info.label | capitalize }}</span>
        </v-col>
      </v-row>

      <!-- NEW WORK ORDER DATA -->
      <v-row v-for="(line, index) in new_work_orders" :key="index">
        <v-col 
          v-for="(info, field_name) in new_wo_info"
          :key="field_name"
          :cols="info.cols"
          class="py-0">
          
          <v-text-field
            v-if="['code', 'project'].includes(field_name)"
            v-model="new_work_orders[index][field_name]"
            autocomplete="off"
            class="input-uppercase">
          </v-text-field>

          <v-autocomplete
            v-if="field_name === 'product'"
            :items="product_list"
            item-text="code"
            return-object
            v-model="new_work_orders[index].product">
          </v-autocomplete>

          <v-text-field
            v-if="field_name === 'qt_planned'"
            single-line
            hide-details
            autocomplete="false"
            :reverse="true"
            type="number"
            v-model="new_work_orders[index].qt_planned">
          </v-text-field>

          <v-dialog
            :value="show_picker === index"
            @input="log($event)"
            @click:outside="show_picker = -1"
            @keydown.esc="show_picker = -1"
            width="300px"
            v-if="field_name === 'due_by'">
            <v-date-picker
              landscape no-title
              show-week
              locale="it-it"
              first-day-of-week="1"
              width="300px"
              @change="setDueBy($event, index)">
            </v-date-picker>
          </v-dialog>

          <v-text-field
            readonly
            v-if="field_name === 'due_by'"
            @click.stop="show_picker = index"
            :value="new_work_orders[index].due_by | shortDateString('it')">
          </v-text-field>
        
        </v-col>
        <v-col cols="1">
          <v-icon v-if="index != 0" @click="deleteRow(index)">close</v-icon> 
        </v-col>
      </v-row>
      <v-btn text class="display medium" @click="addLine">
        + {{ $tc('work_order.add', 1) }}
      </v-btn>
    </template>

    <template v-slot:actions>
        <v-col cols="6">
          <v-btn block :color="$theme.blue" @click="postNewWorkOrder">
            <v-progress-circular indeterminate v-if="loading" />
            <span v-else>
              {{ $tc('save') }}
            </span>
          </v-btn>
        </v-col>
        <v-col cols="6">
          <v-btn block :color="$theme.grey" @click="$router.back()">
            {{ $tc('cancel') }}
          </v-btn>
        </v-col>
    </template>

  </BaseModalForm>

</template>

<script>
import { capitalize } from '@/lib/filters.js'
import BaseModalForm from '@/components/BaseModalForm.vue'

export default {

  name: 'WorkOrderNew',

  components: {
    BaseModalForm
  },

  data () {
    return {
      new_work_orders: [],
      show_picker: -1,
      loading: false
    }
  },

  computed: {
    new_wo_info() {
      return {
        code: {
          label: this.$tc('work_order.wo_code'),
          type: String,
          cols: 2,
          initial_value: ''
        },
        product: {
          label: this.$tc('product.label'),
          type: Object,
          cols: 3,
          initial_value: {}
        },
        qt_planned: {
          label: this.$tc('quantity.long'),
          type: Number,
          cols: 2,
          initial_value: 0
        },
        due_by: {
          label: this.$tc('by'),
          type: Date,
          cols: 2,
          initial_value: ''
        },
        project: {
          label: this.$tc('project'),
          type: String,
          cols: 2,
          initial_value: ''
        }
      }
    },

    product_list() {
      return this.$store.getters.productCatalog()
    }
  },

  methods: {
    addLine() {
      let empty_line = Object.fromEntries(
        Object.entries(this.new_wo_info).map( ([field, value]) => [field, value.initial_value] )
      )
      this.new_work_orders.push(empty_line)
      // this.new_work_orders ++
    },

    postNewWorkOrder() {
      const wo_code_missing = this.new_work_orders.some( wo => !wo.code)
      const quantity_missing = this.new_work_orders.some( wo => wo.qt_planned == 0 )
      const product_missing = this.new_work_orders.some( wo => !wo.product._key )

      console.log({ wo_code_missing, quantity_missing, product_missing })

      if (wo_code_missing || quantity_missing || product_missing)  {
        window.alert(capitalize(this.$tc('form_missing_fields_alert')))
      }

      else {
        let new_records = this.new_work_orders.map( wo => {
        return {
          wo_code: wo.code.toUpperCase(),
          product_key: wo.product._key,
          product_code: wo.product.code,
          product_description: wo.product.description,
          qt_planned: wo.qt_planned,
          due_by: wo.due_by,
          project_code: wo.project
          }
        })
        this.loading = true
        this.$store.dispatch('postWorkOrder', new_records)
        .then( () => {
          this.new_work_orders = []
          this.loading = false
          this.$router.back()
        })
        .catch( err => {
          window.alert(err)
          this.loading = false
        })
      }
    },

    setDueBy(date, index) {
      this.$set(this.new_work_orders[index], 'due_by', date)
      this.show_picker = -1
    },

    deleteRow(index) {
      this.new_work_orders.splice(index,1)
    }
  },

  created() {
    this.$store.dispatch('loadProductList')
    let today = new Date()
    this.new_wo_info.due_by.initial_value =  ''
      + today.getFullYear()
      + '-'
      + (today.getMonth() + 1)
      + '-'
      + today.getDate()
    this.addLine()
  }
}
</script>

<style lang="css" scoped>
</style>
