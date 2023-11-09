<template>
  <div class="fit q-pa-lg">
    <ProductionNotes v-model="phase_notes" :edit-mode="edit_mode" />
  </div>
</template>

<script>
import ProductionNotes from './ProductionNotes.vue'

export default {
  name: 'PhaseNotes',

  components: {
    ProductionNotes
  },

  props: {
    phase: {
      type: Object,
      required: true
    },
    product_data: {
      type: Object,
      required: true
    },
    edit_mode: {
      type: Boolean,
      required: true
    }
  },

  computed: {
    phase_notes: {
      get() {
        return this.phase.production_notes
      },
      set(value) {
        this.$store.commit('UPDATE_PHASE_PRODUCTION_NOTES', {
          phase_index: this.product_data.last_phase,
          content: value
        })
      }
    }
  }
}
</script>

<style lang="css" scoped>
</style>
