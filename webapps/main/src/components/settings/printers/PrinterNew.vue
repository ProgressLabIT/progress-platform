<template>
  <BaseActionFormCard
    :title="$t('add_printer')"
    @submit="addPrinter"
    @cancel="$emit('close')"
  >
    <q-input
      v-model="name"
      :rules="[(value) => !!value || $t('field_required_alert')]"
      hide-bottom-space
      autogrow
      :label="$t('name')"
      filled
      class="q-mt-md"
    />
    <q-input
      v-model="host"
      :rules="[(value) => !!value || $t('field_required_alert')]"
      hide-bottom-space
      autogrow
      :label="$t('host')"
      filled
      class="q-mt-md"
    />
    <q-input
      v-model="port"
      :rules="[(value) => !!value || $t('field_required_alert')]"
      hide-bottom-space
      autogrow
      :label="$t('port')"
      filled
      class="q-mt-md"
    />
  </BaseActionFormCard>
</template>

<script setup>
import { ref } from 'vue';
import BaseActionFormCard from '@/components/BaseActionFormCard.vue';

const name = ref('');
const host = ref('');
const port = ref(80);

const emit = defineEmits(['addPrinter', 'close']);

function addPrinter() {
  emit('addPrinter', { name: name.value, host: host.value, port: port.value });
}
</script>
