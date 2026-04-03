<template>
  <BaseActionFormCard
    :title="mode === 'edit' ? $t('edit_printer') : $t('add_printer')"
    @submit="submit"
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
      v-if="type === 'zpl'"
      v-model.number="dpi"
      type="number"
      min="1"
      :label="$t('printer.dpi')"
      filled
      class="q-mt-md"
      hide-bottom-space
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
import { computed, ref, watch } from 'vue';
import BaseActionFormCard from '@/components/BaseActionFormCard.vue';

const props = defineProps({
  printer: {
    type: Object,
    default: null,
  },
});

const name = ref('');
const host = ref('');
const port = ref(9100);
const type = ref('');
const dpi = ref(203);
const timeout_seconds = ref(5);

const emit = defineEmits(['addPrinter', 'updatePrinter', 'close']);

const mode = computed(() => (props.printer ? 'edit' : 'add'));

watch(
  () => props.printer,
  (printer) => {
    if (printer) {
      name.value = printer.name || '';
      host.value = printer.host || '';
      port.value = printer.port ?? 9100;
      type.value = printer.type || '';
      dpi.value = printer.dpi ?? 203;
      timeout_seconds.value = printer.timeout_seconds ?? 5;
    } else {
      name.value = '';
      host.value = '';
      port.value = 9100;
      type.value = '';
      dpi.value = 203;
      timeout_seconds.value = 5;
    }
  },
  { immediate: true },
);

function submit() {
  const printer = {
    name: name.value,
    host: host.value,
    port: port.value,
    type: type.value,
    timeout_seconds: timeout_seconds.value,
  };
  if (type.value === 'zpl') printer.dpi = dpi.value;

  if (mode.value === 'edit') {
    emit('updatePrinter', printer);
  } else {
    emit('addPrinter', printer);
  }
}
</script>
