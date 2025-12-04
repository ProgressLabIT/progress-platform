<template>
  <SlideUpCard
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    @hide="$emit('update:modelValue', false)"
    height="300px"
  >
    <div class="col column q-gutter-y-sm">
      <div class="text-h3">{{ $t('confirm_empty_position') }}</div>
      <q-space />
      <q-input
        v-model="emptyPositionNotes"
        :label="$t('notes')"
        filled
        autogrow
        class="q-mb-lg"
      />
      <q-btn
        color="theme-blue"
        :label="$t('confirm')"
        :loading="confirming"
        class="full-width"
        @click="confirmEmptyPosition"
      />
      <q-btn
        color="theme-grey"
        :label="$t('cancel')"
        :disable="confirming"
        class="full-width"
        @click="handleCancel"
      />
    </div>
  </SlideUpCard>
</template>

<script setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { Notify } from 'quasar';
import { sendEvent } from '@/composables/event';
import SlideUpCard from '@/components/SlideUpCard.vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  sessionKey: {
    type: String,
    required: true
  },
  positionKey: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:modelValue', 'confirmed', 'cancel']);

const { t: $t } = useI18n();

const emptyPositionNotes = ref('');
const confirming = ref(false);

async function confirmEmptyPosition() {
  confirming.value = true;

  try {
    await sendEvent({
      event_type: 'POSITION_CONFIRMED_EMPTY',
      event_data: {
        session_key: props.sessionKey,
        position_key: props.positionKey,
        notes: emptyPositionNotes.value || null
      }
    });

    Notify.create({
      message: $t('position_confirmed_empty_success'),
      color: 'theme-green',
      position: 'top',
      timeout: 2000
    });

    emit('confirmed');
    emit('update:modelValue', false);
    emptyPositionNotes.value = '';
  } catch (error) {
    console.error('Error confirming empty position:', error);
    // Error notification is already handled by sendEvent
  } finally {
    confirming.value = false;
  }
}

function handleCancel() {
  emit('cancel');
  emit('update:modelValue', false);
  emptyPositionNotes.value = '';
}
</script>

