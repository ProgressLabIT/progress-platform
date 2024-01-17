<template>
  <div class="fit q-pa-md scroll">
    <q-input
      v-model.number="configModel.operatorCost"
      type="number"
      label="Default operator cost"
      :hint="$capitalize($t('user.hourly_cost'))"
      :readonly="!editMode"
      :rules="[(val) => val >= 0 || 'Must be greater than or equal to 0']"
    />

    <q-toggle
      v-model="configModel.allowUnassignedJobs"
      label="Allow working on unassigned jobs"
      :disable="!editMode"
      class="q-mt-md"
    />
  </div>
</template>

<script setup>
defineProps({
  editMode: {
    type: Boolean,
    required: true,
  },
});

const configModel = defineModel({ type: Object, required: true });
</script>
