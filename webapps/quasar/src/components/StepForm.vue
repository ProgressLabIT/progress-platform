<template>
  <div>
    TEST

  </div>
</template>

<script>
// import draggable from 'vuedraggable'

export default {

  name: 'StepForm',

  components: {
    // draggable
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
