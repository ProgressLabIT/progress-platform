<template>
  <div>
    <h5 class="mt-6 mb-6 text-uppercase">
      {{ $tc('phase.form_title') }}
    </h5>
    
    <draggable 
      v-model="input_fields" 
      :disabled="!edit_mode"
      handle=".handle"
      @start="drag = true" 
      @end="drag = false"
      v-bind="$store.state.drag_options">
      <transition-group type="transition" :name="!drag ? 'flip-list' : null">
      <v-row 
        justify="space-between"
        v-for="(field, index) in input_fields" :key="index"
        dense no-gutters class="mb-6">
        <v-col cols="12" class="py-0">

          <v-text-field
            filled single-line dense hide-details
            v-if="field.type=='short'"
            :disabled="!edit_mode"
            :label="$tc('phase.field_name',1, { field_index: index + 1}) | capitalize"
            :name="`field-${index + 1}`"
            :value="field.name"
            class="body-2"
            @change="udpateFieldName(index, $event)"
          ></v-text-field>
          
          <v-textarea
            filled single-line dense auto-grow hide-details
            v-if="field.type=='long'"
            rows="4"
            :disabled="!edit_mode"
            :label="$tc('phase.field_name',1, { field_index: index + 1}) | capitalize"
            :name="`field-${index + 1}`"
            :value="field.name"
            class="body-2"
            @change="udpateFieldName(index, $event)"
          ></v-textarea>
        </v-col> 
        
        <v-col align-self="start" cols="auto" v-if="edit_mode">
          <v-switch 
            dense hide-details  flat
            :input-value="multilineCheck(field.type)"
            :color="$theme.blue"
            class="mt-1"
            @change="updateFieldType(index, $event)">
            <template v-slot:label>
              <span class="body-2">
                {{ $tc('phase.multiline_field') | capitalize }}
              </span>
            </template>
          </v-switch>
        </v-col>  

        <v-col class="d-flex align-end" cols="auto" v-if="edit_mode">
          <v-hover v-slot:default="{ hover }">
            <v-icon 
              class="handle"
              :color="$theme.text_low"
              :style="drag ? 'cursor: grabbing' : 'cursor: grab'">
              drag_handle
            </v-icon>
          </v-hover>
        </v-col>  

        <v-hover v-slot:default="{ hover }" v-if="edit_mode">
          <v-col cols="auto" align-self="end">                
            <button 
              v-if="confirming_delete != index"  
              @click="confirming_delete = index">
              <span 
                :style="`color: ${hover ? $theme.red : $theme.text_low}`"
                class="body-2">
                {{ $tc('phase.delete_field') | capitalize }}
              </span>
              <v-icon :color="hover ? $theme.red : $theme.text_low">close</v-icon>
            </button>

            <v-row v-if="confirming_delete == index" justify="end" class="fill-height"> 
              <v-col cols="auto">
                <v-btn 
                  x-small :color="$theme.red" 
                  @click.stop="deleteField(index)">
                  <v-icon small >delete</v-icon>
                </v-btn>
              </v-col>  

              <v-col cols="auto" class="pl-3">
                <span class="body-2">
                  {{ $tc('confirm_question') | capitalize }}
                </span>
              </v-col>  
            
              <v-col cols="auto">
                <v-btn 
                  x-small :color="$theme.grey"
                  @click.stop="confirming_delete=null">
                  <v-icon small>close</v-icon>
                </v-btn>
              </v-col>  

            </v-row>  
          </v-col>  
        </v-hover>
      </v-row>
    </transition-group>
    </draggable>

    <v-hover v-slot:default="{ hover }" v-if="edit_mode">    
      <v-btn text small class="ml-n3"
        v-if="edit_mode"
        :color="hover ? $theme.blue : $theme.text_high"
        @click="addField">
         + {{ $tc('phase.add_field') | capitalize }}
      </v-btn>
    </v-hover>

  </div>
</template>

<script>
import draggable from 'vuedraggable'

export default {

  name: 'StepForm',

  components: {
    draggable
  },

  props: ['phase_index', 'step_index', 'edit_mode'],

  data() {
    return {
      drag: false,
      confirming_delete: null
    }
  },

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    input_fields: {
      get() {
        const procedure = this.$store.state.process.temp[this.phase_index].steps
        const current_step = procedure[this.step_index]
        return current_step.input_fields
      },

      set(value) {
        let phase_index = this.phase_index
        let step_index = this.step_index
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value })
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
      let phase_index = this.phase_index
      let step_index = this.step_index

      // Handle cases in which input_fields is null
      let new_field_list = this.input_fields ? this.input_fields : []

      new_field_list.push({ type: 'short', name: ''})
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value: new_field_list })
    },

    udpateFieldName(index, text) {
        let phase_index = this.phase_index
        let step_index = this.step_index
        let new_field_list = this.input_fields
        new_field_list[index].name = text
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value: new_field_list })
    },

    updateFieldType(index, multiline) {
        let phase_index = this.phase_index
        let step_index = this.step_index
        let new_field_list = this.input_fields

        let new_type = multiline ? 'long' : 'short'
        new_field_list[index].type = new_type

        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'input_fields', value: new_field_list })  
    },

    deleteField(index) {
      let phase_index = this.phase_index
      let step_index = this.step_index
      let new_field_list = this.input_fields
      new_field_list.splice(index, 1)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value: new_field_list }) 
      this.confirming_delete = null
    }
  }
};
</script>

<style lang="css" scoped>

</style>
