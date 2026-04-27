<template>
  <BaseActionFormCard
    :title="$t('system_counters_title')"
    @submit="save"
    @cancel="$emit('close')"
  >
    <q-select
      v-for="field in fields"
      :key="field.key"
      v-model="values[field.key]"
      filled
      emit-value
      map-options
      hide-bottom-space
      :options="counter_options"
      :label="$t(field.label)"
      :rules="[(value) => !!value || $t('field_required_alert')]"
      class="q-mt-md"
    />
  </BaseActionFormCard>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { api } from '@/boot/axios';
import BaseActionFormCard from '@/components/BaseActionFormCard.vue';

const props = defineProps({
  counterList: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(['close', 'saved']);

const fields = [
  { key: 'tasks', label: 'system_counters_tasks' },
  { key: 'movement_lists', label: 'system_counters_movement_lists' },
  { key: 'work_orders', label: 'system_counters_work_orders' },
  { key: 'counting_sessions', label: 'system_counters_counting_sessions' },
  { key: 'positions', label: 'system_counters_positions' },
];

const values = ref({
  tasks: 'default',
  movement_lists: 'default',
  work_orders: 'default',
  counting_sessions: 'default',
  positions: 'default',
});

const counter_options = computed(() =>
  props.counterList.map((counter) => ({
    label: counter.name,
    value: counter._key,
  })),
);

onMounted(async () => {
  const { data } = await api.get('config');
  const current = data.detail?.system_counters || {};
  for (const field of fields) {
    if (current[field.key]) {
      values.value[field.key] = current[field.key];
    }
  }
});

async function save() {
  await api.patch('config', { system_counters: { ...values.value } });
  emit('saved');
  emit('close');
}
</script>
