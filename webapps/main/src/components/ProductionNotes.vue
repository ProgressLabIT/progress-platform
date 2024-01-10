<template>
  <q-input v-if="editMode" v-model="notes" type="textarea" filled class="fit" />
  <NoDataAlert v-else-if="!notes">
    {{ $t('notes_empty') }}
  </NoDataAlert>
  <div v-else style="white-space: pre-line" class="q-pa-md text-body1">
    {{ notes }}
  </div>
</template>

<script setup>
import NoDataAlert from '@/components/NoDataAlert.vue';

defineProps({
  editMode: {
    type: Boolean,
    required: true,
  },
});

const notes = defineModel({ type: [String, null] });
</script>
