<template>
  <div>TEST</div>
</template>

<script>
import { mapActions } from 'vuex'
import PhaseParameters from '@/components/PhaseParameters.vue'
import PhaseSteps from '@/components/PhaseSteps.vue'
// import PhaseAssignments from '@/components/PhaseAssignments.vue'
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue'
import draggable from 'vuedraggable'


const views_map = [
  'PhaseSteps', 
  'PhaseParameters',
  // 'PhaseAssignments' 
]

export default {

  name: 'ProductionProcess',

  components: {
    PhaseParameters,
    PhaseSteps,
    // PhaseAssignments,
    BaseTooltipIcon,
    draggable,
  },

  data() {
    return {
      views: views_map,
      tab:0,
      new_op: null,
      over_phase: null,
      confirming_delete: null,
      saving: false,
      drag: false,

      show_save_confirmation: false,
      show_cancel_confirmation: false,
    }
  },

  computed: {
    
    product_key() {
      return this.$route.params.product_key
    }, 

    product_data() {
      return this.$store.getters.productData(this.product_key)
    },

    edit_mode: {
      get() {
        return this.$store.state.product.edit_modes.process
      },
      set(value) {
        this.$store.commit('TOGGLE_EDIT_MODE', { view: 'process', value })
      }
    },

    operations() {
      return this.$store.state.process.operations.slice().sort()
    },

    current_phase: {
      get() {
        return this.product_data.last_phase
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT_NAV_STATE', 
          { _key: this.product_key, last_phase: value}
        )
      }
    },

    process: {
      get() {
        return this.$store.state.process.temp
      },

      set(value) {
        this.$store.commit('UPDATE_PROCESS', value)
      }
    },

  },

  methods: {
    ...mapActions(['loadProductDetails']),

    toggleEdit() {
      this.edit_mode = true
    },

    cancelChanges() {
      this.$store.commit('CANCEL_PROCESS_CHANGES')
      this.show_cancel_confirmation = true
      this.edit_mode = false
    },

    addPhase(new_operation) {
      let new_process = this.process
      new_process.push({ 
        alias: new_operation.name, 
        operation_key: new_operation._key, 
        product_key: this.product_key,
        params: new_operation.default_phase_parameters,
        steps: []
      })
      this.$store.commit('UPDATE_PROCESS', new_process)
      this.current_phase = new_process.length - 1

      // push blur to the end of the stack to let animation run properly
      setTimeout(() => {
        this.new_op = null
        this.$refs.add_phase.blur()
      }, 1)
    },

    deletePhase(phase_index) {
      this.$store.commit('DELETE_PHASE', phase_index)
      this.confirming_delete = null
    },

    updateActivePhaseIndex(event) {
      let moved = event.moved
      if (this.current_phase == moved.oldIndex) {
        this.current_phase = moved.newIndex
      }
      else if ( moved.oldIndex < this.current_phase 
                && moved.newIndex > this.current_phase ) {
        this.current_phase = this.current_phase - 1
      }
      else if ( moved.oldIndex > this.current_phase 
                && moved.newIndex < this.current_phase ) {
        this.current_phase = this.current_phase + 1
      }
      // ADD HERE REORDERING OF last_steps MAP
      let new_steps_map = this.product_data.last_steps
      new_steps_map.splice(moved.oldIndex, 1)
      new_steps_map.splice(moved.newIndex, 0, moved.element)

      this.$store.commit('UPDATE_PRODUCT_NAV_STATE', { last_steps: new_steps_map })
    },

    saveChanges() {
      this.saving = true
      let process_update = {
        product_key: this.product_key,
        new_process: this.process
      }
      this.$store.dispatch('saveTempProcess', process_update)
        .then(() => {
        // Show progress long enough the let user notice something is going on
        // even if the update is instantaneous
          setTimeout(() => {
            this.show_save_confirmation = true
            this.saving = false
            this.edit_mode = false
          }, 500)
        }).catch(err => {
          window.alert(err)
          this.saving = false
        })
    },
  },
};
</script>

<style lang="css" scoped>
</style>
