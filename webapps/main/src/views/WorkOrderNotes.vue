<template>
  <div class="fit q-pa-lg">
    <q-input
      filled
      autogrow
      :model-value="wo_data.notes"
      @update:model-value="updateNotes"
      debounce="1000"
      class="fit"
    >
    </q-input>
  </div>
</template>

<script>
export default {
  name: 'WorkOrderNotes',

  props: {
    wo_data: {
      type: Object,
      required: true,
    },
  },

  methods: {
    async updateNotes(value) {
      const update = { wo_key: this.wo_data._key, notes: value };
      await this.$store.dispatch('updateWorkOrder', update);
      await this.$store.dispatch('loadWorkOrderData', update.wo_key);
    },
  },

  created() {
    this.notes = this.wo_data.notes;
  },
};
</script>

<style lang="css" scoped></style>
