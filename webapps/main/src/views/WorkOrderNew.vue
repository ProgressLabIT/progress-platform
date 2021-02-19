<template>
  <BaseModalForm @submit="postNewWorkOrder" max_width="700px" >
    <template v-slot:title>
      {{ $tc('work_order.new') }}
    </template>
    
    <template v-slot:form>
      <h4 class="weight-bold text-uppercase">
        {{ $tc('work_order.wo_code') }}
      </h4>
      <v-text-field v-model="wo_code">
      </v-text-field>

      <h4 class="weight-bold text-uppercase">
        {{ $tc('work_order.wo_line.short', 2) }}
      </h4>

      <v-row>
        <v-col 
          v-for="(info, field_name) in wo_line_info" 
          :key="field_name"
          :cols="info.cols"
          class="pb-0">
          <span>{{ info.label | capitalize }}</span>
        </v-col>
      </v-row>

      <v-row v-for="(line, index) in wo_lines" :key="index">
        <v-col 
          v-for="(info, field_name) in wo_line_info" 
          :key="field_name"
          :cols="info.cols"
          class="py-0">
          
          <v-dialog 
            :value="show_picker === index" 
            @input="log($event)"
            @click:outside="show_picker = -1"
            @keydown.esc="show_picker = -1"
            width="300px">
            <v-date-picker
              landscape no-title
              show-week
              locale="it-it"
              first-day-of-week="1"
              width="300px"
              v-if="field_name === 'due_by'"
              @change="setDueBy($event, index)">
            </v-date-picker>
          </v-dialog>

          <v-text-field 
            readonly              
            v-if="field_name === 'due_by'"
            @click.stop="show_picker = index"
            :value="wo_lines[index].due_by | shortDateString('it')">
          </v-text-field>         

          <v-autocomplete
            v-else-if="field_name === 'product'"
            :items="product_list"
            item-text="code"
            return-object
            v-model="wo_lines[index].product">
          </v-autocomplete>

          <v-text-field 
            v-else 
            single-line 
            hide-details
            autocomplete="false"
            :reverse="info.type === Number"
            :type="field_name === 'qt_planned' ? 'number' : '' "
            v-model="wo_lines[index][field_name]">
          </v-text-field>
        
        </v-col>
        <v-col cols="1">
          <v-icon v-if="index != 0" @click="deleteRow(index)">close</v-icon> 
        </v-col>
      </v-row>
      <v-btn text class="display medium" @click="addLine">
        + {{ $tc('work_order.add_line', 1) }}
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
import BaseModalForm from '@/components/BaseModalForm.vue'

export default {

  name: 'WorkOrderNew',

  components: {
    BaseModalForm
  },

  data () {
    return {
      wo_code: '',
      wo_lines: [],
      show_picker: -1,
      loading: false
    }
  },

  computed: {
    wo_line_info() {
      return {
        product: {
          label: this.$tc('product.label'),
          type: Object,
          cols: 5,
          initial_value: {}
        },
        qt_planned: {
          label: this.$tc('quantity.long'),
          type: Number,
          cols: 3,
          initial_value: 0
        },
        due_by: {
          label: this.$tc('by'),
          type: Date,
          cols: 3,
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
        Object.entries(this.wo_line_info).map( ([field, value]) => [field, value.initial_value] )
      )
      this.wo_lines.push(empty_line)
      // this.wo_lines ++
    },

    postNewWorkOrder() {
      let new_records = this.wo_lines.map( (line, index) => {
        return {
          wo_code: this.wo_code,
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

<style lang="css" scoped>
</style>