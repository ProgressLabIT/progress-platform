<template>
  <q-dialog
    v-model="localShow"
    backdrop-filter="brightness(0.3)"
    @hide="emit('close')">
    <q-card square class="surface1 q-pa-md">
      <q-card-section class="text-h3 highlight">
        <slot></slot>
      </q-card-section>

      <q-card-section>
        <div class="row justify-between q-gutter-xl">
          <q-btn
            :color="cancel_color || 'theme-grey'"
            :label="cancel_prompt || $t('cancel')"
            @click="emit('close')"
          >
          </q-btn>
          <q-btn
            :color="confirm_color || 'theme-blue'"
            :label="confirm_prompt || $t('confirm')"
            @click="emit('confirm')"
          >
          </q-btn>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t: $t } = useI18n()

// Props
const props = defineProps({
  show: {
    type: Boolean,
    required: true,
  },
  confirm_color: {
    type: String,
    default: undefined,
  },
  confirm_prompt: {
    type: String,
    default: undefined,
  },
  cancel_color: {
    type: String,
    default: undefined,
  },
  cancel_prompt: {
    type: String,
    default: undefined,
  }
})

// Events
const emit = defineEmits(['close', 'confirm'])

// Local reactive data
const localShow = ref(props.show)

// Watch for prop changes
watch(() => props.show, (newVal) => {
  localShow.value = newVal
})
</script>