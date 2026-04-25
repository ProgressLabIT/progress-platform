<template>
  <div>
    <q-tabs
      :model-value="sub"
      dense
      align="left"
      inline-label
      narrow-indicator
      class="text-secondary q-px-lg"
      @update:model-value="(v) => $emit('update:sub', v)"
    >
      <q-tab
        name="jobs"
        icon="mdi-briefcase-variant-outline"
        :label="$capitalize($t('user_hub.sub_jobs'))"
      />
      <q-tab
        name="tasks"
        icon="mdi-check-circle-outline"
        :label="$capitalize($t('user_hub.sub_tasks'))"
      />
    </q-tabs>
    <q-separator />
    <q-tab-panels
      :model-value="sub"
      animated
      keep-alive
      class="bg-transparent"
    >
      <q-tab-panel name="jobs" class="q-px-lg q-pt-md" tabindex="-1">
        <UserJobsList ref="jobsRef" />
      </q-tab-panel>
      <q-tab-panel name="tasks" class="q-px-lg q-pt-md" tabindex="-1">
        <UserTasksList ref="tasksRef" />
      </q-tab-panel>
    </q-tab-panels>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import UserJobsList from '@/components/user-hub/UserJobsList.vue';
import UserTasksList from '@/components/user-hub/UserTasksList.vue';

const props = defineProps({ sub: { type: String, default: 'jobs' } });
defineEmits(['update:sub']);

const jobsRef = ref(null);
const tasksRef = ref(null);

const loading = computed(
  () => jobsRef.value?.loading || tasksRef.value?.loading || false,
);

function refreshActive() {
  if (props.sub === 'tasks') {
    tasksRef.value?.refresh?.();
  } else {
    jobsRef.value?.refresh?.();
  }
}

defineExpose({ loading, refreshActive });
</script>
