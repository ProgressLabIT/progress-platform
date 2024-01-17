<template>
  <div class="fit q-pa-md scroll">
    <ProcessParameters
      v-model="configModel.operationParameters"
      process-has-steps
      :edit-mode="editMode"
    />
  </div>
</template>

<script setup>
import ProcessParameters from '@/components/ProcessParameters.vue';

defineProps({
  editMode: {
    type: Boolean,
    required: true,
  },
});

const configModel = defineModel({ type: Object, required: true });
</script>
