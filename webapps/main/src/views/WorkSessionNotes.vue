<template>
  <div class="fit column">
    <template v-if="notes.length">
      <div
        v-for="note in notes"
        :key="note.type"
        class="surface2 shadow-2 multiline-text col column q-px-md q-pt-md"
      >
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
import NoDataAlert from '@/components/NoDataAlert.vue';

export default {
  name: 'WorkSessionNotes',

  components: {
    NoDataAlert,
  },

  props: {
    job: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      note_types: ['order', 'phase', 'product'],
    };
  },

  computed: {
    notes() {
      let notes = [];
      this.note_types.forEach((type) => {
        const value = this.job[`${type}_notes`];
        if (value)
          notes.push({
            type,
            label: this.$t(`notes_${type}`),
            value,
          });
      });
      return notes;
    },
  },
};
</script>

<style lang="css" scoped></style>
