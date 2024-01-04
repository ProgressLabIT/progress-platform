<template>
  <BaseActionCard :title="title">
    <template #title v-if="$slots.title">
      <slot name="title" />
    </template>

    <q-form
      :id="uniqueFormId"
      :greedy="greedy"
      class="column no-wrap scroll"
      @submit="emit('submit')"
      @validation-error="emit('validation-error', $event)"
    >
      <slot />
    </q-form>

    <template #actions>
      <!-- We are passing form uuid to be able to connect the custom button to the form -->
      <slot name="actions" :unique-form-id="uniqueFormId">
        <q-btn
          type="submit"
          :form="uniqueFormId"
          :label="submitLabel ?? $t('save')"
          :color="submitColor"
        />

        <q-btn
          :label="cancelLabel ?? $t('cancel')"
          :color="cancelColor"
          @click="emit('cancel')"
        />
      </slot>
    </template>
  </BaseActionCard>
</template>

<script setup>
import { uid } from 'quasar'
import BaseActionCard from '@/components/BaseActionCard.vue'

defineProps({
  title: {
    type: String,
    required: false
  },
  greedy: {
    type: Boolean,
    default: false
  },
  submitLabel: {
    type: String,
    required: false
  },
  submitColor: {
    type: String,
    required: false,
    default: 'theme-blue'
  },
  cancelLabel: {
    type: String,
    required: false
  },
  cancelColor: {
    type: String,
    required: false,
    default: 'theme-grey'
  },
})

const emit = defineEmits(['submit', 'validation-error', 'cancel'])

// Avoids collisions when there's more than one active component instance at the same time
const uniqueFormId = `dialog-form-${uid()}`
</script>
