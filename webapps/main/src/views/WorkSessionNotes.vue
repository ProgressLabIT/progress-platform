<template>
  <div class="fit column q-gutter-md q-pt-md q-pl-md">
    <template v-if="notes.length">
      <div v-for="note in notes"
        class="surface2 shadow-2 multiline-text col column q-px-md q-pt-md">
        <div class="text-uppercase text-h5 q-mb-md col-auto">
          {{ note.label }}
        </div>
        <div class="col scroll q-pb-md">
          {{ note.value }}
        </div>
      </div>
    </template>

    <NoDataAlert v-else>
      {{ $t('notes_empty') }}
    </NoDataAlert>
  </div>
</template>

<script>
import NoDataAlert from '@/components/NoDataAlert.vue'

export default {

  name: 'WorkSessionNotes',

  components: {
    NoDataAlert
  },

  props: {
    job: {
      type: Object,
      required: true
    }
  },

  data() {
    return {
      note_types: ['order', 'phase', 'product']
    }
  },

  computed: {
    notes() {
      let notes = []
      this.note_types.forEach(t => {
        const value = this.job[`${t}_notes`]
        if (value) notes.push({
          label: this.$t(`notes_${t}`),
          value
        })
      })
      return notes
    }
  }
}
</script>

<style lang="css" scoped>
</style>
