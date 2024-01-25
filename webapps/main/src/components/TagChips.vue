<template>
  <q-chip
    v-for="tag in tags"
    :key="tag._key"
    :label="tag.name"
    :color="tag.color ?? defaultColor"
    :dense="dense"
  >
    <q-tooltip v-if="tag.description">
      {{ tag.description }}
    </q-tooltip>
  </q-chip>
</template>

<script setup>
defineProps({
  tags: {
    type: Array,
    required: true,
  },
  dense: {
    type: Boolean,
    default: false,
  },
  defaultColor: {
    type: String,
    default: 'theme-grey',
  },
});
</script>
