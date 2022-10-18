<template>
  <v-container fluid class="scroll pt-8 px-12" :style="'max-height:'+height+'px'">
    
    <v-card-title class="display highlight px-0 pt-0 pb-3 nowrap">
      {{ step.title }}
    </v-card-title>
    <v-card-subtitle 
      class="px-0 pb-1 mb-6">
      {{ step.description }}
    </v-card-subtitle>


    <template v-for="(field, index) in step_form">
      <v-text-field 
        :value="field_data[index]"
        @change="updateField(index, $event)"
        @input="debouncedFieldUpdate(index, $event)"
        outlined
        :disabled="!job_active  || batch_step.done"
        v-if="field.type=='short'" 
        :label="field.name"
        :key="index">
      </v-text-field>
      
      <v-textarea 
        :value="field_data[index]"
        @change="updateField(index, $event)"
        @input="debouncedFieldUpdate(index, $event)"
        outlined
        :disabled="!job_active || batch_step.done"
        v-if="field.type=='long'" 
        :label="field.name"
        :key="index">
      </v-textarea>

    </template>
  </v-container>
</template>

<script>
import { debounce as _debounce } from 'lodash'
export default {

  name: 'JobForm',

  props: {
    step: {
      type: Object,
      required: true,
    },
    height: {
      type: Number,
      required: true
    }
  },

  data () {
    return {
      // values: []
    }
  },

  computed: {
    step_form() {
      return this.step.input_fields
    },

    job_active() {
      return this.$store.state.traceability.working_job_data.active
    },

    batch_step() {
      return this.$store.getters.getBatchStep(this.step._key)
    },

    field_data() {
      const data = this.batch_step.user_data
      return data ? data : []
    }
  },

  methods: {
    updateField(index, value) {
      const field_data = {
        step_key: this.step._key,
        value_index: index,
        value
      }
      this.$store.commit('UPDATE_STEP_USER_DATA', field_data)
    }
  },

  created() {
    this.debouncedFieldUpdate = _debounce(this.updateField, 1000)
  }
}
</script>

<style lang="css" scoped>
</style>