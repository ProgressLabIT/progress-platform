<template>
  <template v-if="!editMode">
    <NoDataAlert v-if="!notes">
      {{ $t('notes_empty') }}
    </NoDataAlert>
    <div v-else style="white-space: pre-line" class="q-pa-md text-body1">
      {{ notes }}
    </div>
  </template>
  <q-input
    v-else
    v-model="notes"
    type="textarea"
    filled
    class="fit"
  />
</template>

<script setup>
import { computed } from 'vue'
import NoDataAlert from '@/components/NoDataAlert.vue'

// TODO: Use defineModel macro to simplify the model related logic (Vue 3.3+)

const props = defineProps({
  modelValue: {
    type: String,
    required: true
  },
  editMode: {
    type: Boolean,
    required: true
  },
})
const emit = defineEmits(['update:modelValue'])

const notes = computed({
  get: () => props.modelValue,
  set(value) {
    emit('update:modelValue', value)
  }
})
</script>
