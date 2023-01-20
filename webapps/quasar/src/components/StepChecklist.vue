<template>
  <div>
    TEST
  </div>
</template>

<script>
// import {debounce as _debounce} from 'lodash/fp'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
// import draggable from 'vuedraggable'

export default {

  name: 'StepChecklist',

  components: {
    BaseTooltipIcon,
    // draggable
  },

  props: ['phase_index', 'step_index', 'edit_mode'],

  data() {
    return {
      over_row: null,
      drag: false,
      confirming_delete: null
    }
  },

  computed: {

    product_key() {
      return this.$route.params.item_key
    },

    current_step() {
      let procedure = this.$store.state.process.temp[this.phase_index].steps
      return procedure[this.step_index]
    },

    step_checks: {
      get() {
        return this.current_step.checks
      },

      set(value) {
        let phase_index = this.phase_index
        let step_index = this.step_index

        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value })
      }
    }
  },

  methods: {

    addCheck() {
      let phase_index = this.phase_index
      let step_index = this.step_index

      let new_step = this.current_step
      new_step.checks.push('')
      // Handle cases in which step_checks is null

      this.$store.commit('ADD_OR_UPDATE_STEP', { phase_index, step_index, step_data: new_step })
    },

    udpateCheck(index, text) {
        let phase_index = this.phase_index
        let step_index = this.step_index
        let new_checklist = this.step_checks
        new_checklist[index] = text
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value: new_checklist })
    },

    deleteCheck(index) {
      let phase_index = this.phase_index
      let step_index = this.step_index
      let new_checklist = this.step_checks
      new_checklist.splice(index, 1)
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'checks', value: new_checklist }) 
      this.confirming_delete = null
    }
  },
};
</script>

<style lang="css" scoped>
</style>
