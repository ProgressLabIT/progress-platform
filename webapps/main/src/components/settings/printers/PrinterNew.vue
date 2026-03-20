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
    <q-select
      v-model="type"
      :options="[{ label: 'ZPL', value: 'zpl' }, { label: 'PDF', value: 'pdf' }]"
      emit-value
      map-options
      :rules="[(value) => !!value || $t('field_required_alert')]"
      hide-bottom-space
      :label="$t('printer.type')"
      filled
      class="q-mt-md"
    />
    <q-input
      v-model.number="timeout_seconds"
      type="number"
      min="1"
      :label="$t('printer.timeout_seconds')"
      filled
      class="q-mt-md"
      hide-bottom-space
    />
  </BaseActionFormCard>
</template>

<script setup>
import { ref } from 'vue';
import BaseActionFormCard from '@/components/BaseActionFormCard.vue';

const name = ref('');
const host = ref('');
const port = ref(80);
const type = ref('');
const timeout_seconds = ref(5);

const emit = defineEmits(['addPrinter', 'close']);

function addPrinter() {
  emit('addPrinter', { name: name.value, host: host.value, port: port.value, type: type.value, timeout_seconds: timeout_seconds.value });
}
</script>
