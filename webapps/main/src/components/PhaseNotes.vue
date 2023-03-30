<template>
  <div class="fit q-pa-lg">
    <template v-if="!edit_mode">
      <div v-if="!!phase_notes" style="white-space: pre-line" class="q-pa-md text-body1">
        {{ phase_notes }}
      </div>
      <NoDataAlert v-else>
        {{ $t('notes_empty') }}
      </NoDataAlert>
    </template>
    <q-input v-else filled type="textarea" v-model="phase_notes" class="fit" />
  </div>
</template>

<script>
import NoDataAlert from '@/components/NoDataAlert.vue'
export default {

  name: 'PhaseNotes',

  components: {
    NoDataAlert
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
  },

  mounted() {
    console.log(this.phase, this.phase.production_notes, this.phase_notes)
  }
}
</script>

<style lang="css" scoped>
</style>
