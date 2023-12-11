<template>
  <div class="fit q-pa-lg">
    <q-input
      filled
      autogrow
      :model-value="wo_data.notes"
      debounce="1000"
      class="fit"
      @update:model-value="updateNotes"
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

  created() {
    this.notes = this.wo_data.notes;
  },

  methods: {
    async updateNotes(value) {
      const update = { wo_key: this.wo_data._key, notes: value };
      await this.$store.dispatch('updateWorkOrder', update);
      await this.$store.dispatch('loadWorkOrderData', update.wo_key);
    },
  },
};
</script>

<style lang="css" scoped></style>
