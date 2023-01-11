<template>
  <div>TEST</div>
</template>

<script>
import StepInstruction from '@/components/StepInstruction.vue'
import StepChecklist from '@/components/StepChecklist.vue'
import StepForm from '@/components/StepForm.vue'
import draggable from 'vuedraggable'

export default {

  name: 'PhaseSteps',

  props: ['edit_mode', 'phase', 'product_data'],

  components: {
    StepInstruction,
    StepChecklist,
    StepForm,
    draggable
  },

  data() {
    return {
      step_types: ['instruction', 'checklist', 'form'],
      detail_box_height: '79vh',
      over_delete: false,
      confirming_delete: false,
      drag: false,
    };
  },

  computed: {
    product_key() {
      return this.$route.params.product_key
    },

    current_phase() {
      return this.product_data.last_phase
    },

    current_steps_map: {
      get() {
        return this.product_data.last_steps
      },

      set(value) {
        this.$store.commit(
          'UPDATE_PRODUCT_NAV_STATE', 
          { _key: this.product_key, last_steps: value}
        )
      }
    },

    current_step_index: {
      get() {
        return this.current_steps_map[this.current_phase]
      },
      set(value) {
        this.current_steps_map[this.current_phase] = value
      }
    },

    procedure: {
      get() {
        return this.phase ? this.phase.steps : null
      },

      set(value) {
        let phase_index = this.current_phase
        this.$store.commit('UPDATE_PROCEDURE', { phase_index, procedure: value })
      }
    },

    render_steps() {
      return this.procedure != null && this.procedure.length
        ? true
        : false
    },

    current_step() {
      const last_step_viewed = this.procedure[this.current_step_index]
      return typeof last_step_viewed === 'undefined' ? 0 : last_step_viewed
    },

    step_title: {
      get() {
        return this.current_step.title
      },

      set(value) {
        let phase_index = this.current_phase
        let step_index = this.current_steps_map[phase_index]
        this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'title', value })
      }
    },

    step_desc() {
        return this.current_step.description
    },
  },

  methods: {
    stepIcon(step_type) {
      switch (step_type) {
        case 'instruction': return 'playlist_add_check';
        case 'checklist': return 'mdi-format-list-checks';
        case 'form': return 'mdi-playlist-edit';
        default: return '';
      }
    },

    step_component() {
      const step_index = this.current_steps_map[this.current_phase]
      const step = typeof step_index == 'undefined' ? 0 : step_index

      switch (this.procedure[step].type) {
        case 'instruction': return 'StepInstruction';
        case 'checklist': return 'StepChecklist';
        case 'form': return 'StepForm';
        default: return '';
      }
    },

    updateDesc(value) {
      let phase_index = this.current_phase
      let step_index = this.current_steps_map[phase_index]
      this.$store.commit('UPDATE_STEP_DETAILS', { phase_index, step_index, field: 'description', value })
    },

    addStep(type) {
      let phase_index = this.current_phase
      let step_index = this.procedure ? this.procedure.length : 0
      let step_data = {
        type: type,
        title: '',
        description: '', 
        checks: [],
        input_fields: [],
        media: []
      }
      this.$store.commit('ADD_OR_UPDATE_STEP', { phase_index, step_index, step_data})
      let new_step_index = this.procedure.length - 1
      this.current_step_index = new_step_index
    },

    showConfirmDelete() {
      this.confirming_delete = true
      this.over_delete = false
    },

    deleteStep(step_index) {
      const phase_index = this.current_phase
      const len = this.procedure.length
      // if step to be deleted is last, set next step index to second to last
      if (step_index == len-1) {
        const next_step_index = len > 1 ? len - 2 : 0
        this.current_steps_map[this.current_phase] = next_step_index
      }
      this.$store.commit('DELETE_STEP', { phase_index, step_index })
      this.confirming_delete = false

    },

    updateTabIndex(event) {
      let moved = event.moved
      if (this.current_step_index == moved.oldIndex) {
        this.current_steps_map[this.current_phase] = moved.newIndex
      }
      else if ( moved.oldIndex < this.current_step_index 
                && moved.newIndex > this.current_step_index ) {
        let new_step_index = this.current_step_index - 1
        this.current_steps_map[this.current_phase] = new_step_index
      }
      else if ( moved.oldIndex > this.current_step_index 
                && moved.newIndex < this.current_step_index ) {
        let new_step_index = this.current_step_index + 1
        this.current_steps_map[this.current_phase] = new_step_index
      }
    }
  },
};
</script>

<style lang="css" scoped>
</style>
