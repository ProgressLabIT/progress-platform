<template>
  <div class="fit q-pa-lg scroll">
    <div class="row item-center q-mb-md">
      <div class="text-h2 display">{{ title }}</div>

      <q-space />

      <template v-if="editMode">
        <q-btn
          type="submit"
          form="settings-form"
          size="12px"
          color="theme-blue"
          class="q-ml-auto"
          :label="$t('save')"
        />
        <q-btn
          size="12px"
          class="q-ml-md"
          color="theme-grey"
          :label="$t('cancel')"
          @click="cancel"
        />
      </template>
      <BaseTooltipIcon
        v-else
        icon="mdi-pencil"
        :tooltip="$capitalize($t('edit'))"
        :color="$theme.blue"
        @icon-click="editMode = true"
      />
    </div>

    <q-form id="settings-form" @submit="save">
      <slot v-bind="{ editMode }" />
    </q-form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import BaseTooltipIcon from '@/components/BaseTooltipIcon.vue';

defineProps({
  title: {
    type: String,
    required: true,
  },
});

const emit = defineEmits(['save', 'cancel']);

const editMode = ref(false);

function save() {
  editMode.value = false;
  emit('save');
}

function cancel() {
  editMode.value = false;
  emit('cancel');
}
</script>
