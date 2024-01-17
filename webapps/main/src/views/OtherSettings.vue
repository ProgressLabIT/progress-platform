<template>
  <div class="fit q-pa-md scroll">
    <q-input
      v-model.number="configModel.operatorCost"
      type="number"
      :label="$t('settings.operatorCost.label')"
      :hint="$capitalize($t('user.hourly_cost'))"
      :readonly="!editMode"
      :rules="[(val) => val >= 0 || $t('settings.operatorCost.mustBePositive')]"
    />

    <q-toggle
      v-model="configModel.allowUnassignedJobs"
      :label="$t('settings.allowUnassignedJobs')"
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
