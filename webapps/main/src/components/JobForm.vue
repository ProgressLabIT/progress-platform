<template>
  <v-container fluid class="scroll pt-12 px-12" :style="'max-height:'+height+'px'">
    <template v-for="(field, index) in step_form">
      <v-text-field 
        v-model="values[index]"
        outlined
        v-if="field.type=='short'" 
        :label="field.name"
        :key="index">
      </v-text-field>
      
      <v-textarea 
        v-model="values[index]"
        outlined
        v-if="field.type=='long'" 
        :label="field.name"
        :key="index">
      </v-textarea>

    </template>
  </v-container>
</template>

<script>
export default {

  name: 'JobForm',

  props: {
    step: {
      type: Object,
      required: true,
    }
  },

  data () {
    return {
      values: []
    }
  },

  computed: {
    step_form() {
      return this.step.input_fields
    },
  }
}
</script>

<style lang="css" scoped>
</style>