<template>
  <div class="column q-gutter-y-md">
    <div class="row q-gutter-x-md items-center">
      <div class="text-h2">{{ $t('position') }}</div>
      <q-chip color="theme-grey" class="text-body1 highlight">{{ props.position.code }}</q-chip>
    </div>
    <q-btn color="theme-blue" :label="$t('select_container')" class="full-width" @click="emit('select-container')" />
    <q-btn color="theme-blue" :label="$t('select_contents')" class="full-width" @click="emit('select-contents')" />
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n';

const { t: $t } = useI18n();

const props = defineProps({
  position: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['select-contents', 'select-container']);
</script>

