<template>
  <v-container fluid class="scroll pt-12 px-12" :style="'max-height:'+height+'px'">
    <template v-for="(field, index) in step_form">
      <v-text-field 
        :value="field_data[index]"
        @input="debouncedFieldUpdate(index, $event)"
        outlined
        :disabled="!job_active"
        v-if="field.type=='short'" 
        :label="field.name"
        :key="index">
      </v-text-field>
      
      <v-textarea 
        :value="field_data[index]"
        @input="debouncedFieldUpdate(index, $event)"
        outlined
        :disabled="!job_active"
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

    field_data() {
      return this.$store.getters.getIterationStepUserData(this.step._id)
    }
  },

  methods: {
    updateField(index, value) {
      const field_data = {
        step_id: this.step._id,
        value_index: index,
        value
      }
      this.$store.commit('UPDATE_USER_DATA', field_data)
    }
  },

  created() {
    this.debouncedFieldUpdate = _debounce(this.updateField, 1000)
  }
}
</script>

<style lang="css" scoped>
</style>