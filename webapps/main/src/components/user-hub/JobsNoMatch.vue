<template>
  <div class="column items-center q-pa-xl text-low">
    <q-icon name="mdi-filter-off-outline" size="64px" aria-hidden="true" />
    <div class="text-body2 q-mt-md">{{ $t('user_hub.jobs_no_match') }}</div>
    <q-btn
      flat
      dense
      color="primary"
      :label="$t('filters_reset')"
      class="q-mt-md"
      @click="$emit('clear')"
    />
  </div>
</template>

<script setup>
defineEmits(['clear']);
</script>
