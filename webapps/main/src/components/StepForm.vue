<template>
  <div>
    <h5 class="mt-6 mb-6 text-uppercase">Campi modulo</h5>
    
    <draggable v-model="input_fields">
      <v-row 
        v-for="(field, index) in input_fields" :key="index"
        dense no-gutters class="mb-6">
        <v-col cols="12" class="py-0">

          <v-text-field
            filled single-line dense hide-details
            v-if="field.type=='short'"
            :label="`Nome campo ${index + 1}`"
            :name="`field-${index + 1}`"
            :value="field.name"
            class="body-2"
            @change="udpateFieldName(index, $event)"
          ></v-text-field>
          
          <v-textarea
            filled single-line dense auto-grow hide-details
            v-if="field.type=='long'"
            rows="4"
            :label="`Nome campo ${index + 1}`"
            :name="`field-${index + 1}`"
            :value="field.name"
            class="body-2"
            @change="udpateFieldName(index, $event)"
          ></v-textarea>
        </v-col> 
        
        <v-col align-self="start">
          <v-switch 
            dense hide-details  flat
            :input-value="multilineCheck(field.type)"
            :color="$theme.blue"
            class="mt-1"
            @change="updateFieldType(index, $event)">
            <template v-slot:label>
              <span class="body-2">
                Multiriga
              </span>
            </template>
          </v-switch>
        </v-col>  

        <v-spacer></v-spacer> 
        
        <v-hover v-slot:default="{ hover }">
          <v-col cols="auto" align-self="end">                
            <button @click="deleteField(index)">
              <span 
              :style="`color: ${hover ? $theme.red : $theme.whitelow}`"
              class="body-2"
              >Elimina campo</span>
            <v-icon
              :color="hover ? $theme.red : $theme.whitelow"
              >close</v-icon>
            </button>
          </v-col>  
        </v-hover>
      </v-row>
    </draggable>

    <button
        :color="$theme.whitehigh"
        class="py-1 weight-medium highlight"
        style="font-size: 14px"
        @click="addField"
        >
        + Aggiungi campo
    </button>

  </div>
</template>

<script>
import draggable from 'vuedraggable'

export default {

  name: 'StepForm',

  components: {
    draggable
  },

  props: ['phase_no', 'step_no'],

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    input_fields: {
      get() {
        const procedure = this.$store.state.current_product.process[this.phase_no].steps
        const current_step = procedure[this.step_no]
        return current_step.input_fields
      },

      set(value) {
        let phase_no = this.phase_no
        let step_no = this.step_no
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'input_fields', value })
      }
    }
  },

  methods: {

    multilineCheck(field_type) {
      switch (field_type) {
        case 'short': return false
        case 'long': return true 
      }
    },

    addField() {
      let phase_no = this.phase_no
      let step_no = this.step_no

      // Handle cases in which input_fields is null
      let new_field_list = this.input_fields ? this.input_fields : []

      new_field_list.push({ type: 'short', name: ''})
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'input_fields', value: new_field_list })
    },

    udpateFieldName(index, text) {
        let phase_no = this.phase_no
        let step_no = this.step_no
        let new_field_list = this.input_fields
        new_field_list[index].name = text
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'input_fields', value: new_field_list })
    },

    updateFieldType(index, multiline) {
        let phase_no = this.phase_no
        let step_no = this.step_no
        let new_field_list = this.input_fields

        let new_type = multiline ? 'long' : 'short'
        new_field_list[index].type = new_type

        this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'input_fields', value: new_field_list })  
    },

    deleteField(index) {
      let phase_no = this.phase_no
      let step_no = this.step_no
      let new_field_list = this.input_fields
      new_field_list.splice(index, 1)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_no, step_no, field: 'checks', value: new_field_list }) 
    }
  }
};
</script>

<style lang="css" scoped>
</style>
