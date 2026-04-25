<template>
  <div>
    <q-inner-loading :showing="loading && tasks.length === 0">
      <q-spinner-dots size="50px" color="theme-blue" />
    </q-inner-loading>
    <TasksEmpty v-if="!loading && tasks.length === 0" />
    <q-list v-else separator class="q-mt-sm">
      <q-item
        v-for="task in tasks"
        :key="task._key"
        clickable
        v-ripple
        @click="openTask(task)"
      >
        <q-item-section avatar>
          <q-icon
            :name="task.is_overdue ? 'mdi-alert-circle-outline' : 'mdi-check-circle-outline'"
            :color="task.is_overdue ? 'theme-orange' : 'theme-blue'"
            aria-hidden="true"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label lines="1" class="text-high">{{ task.title }}</q-item-label>
          <q-item-label
            caption
            lines="1"
            :class="task.is_overdue ? 'text-theme-orange' : 'text-low'"
          >
            {{ relative(task.due_by) }}
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-icon name="mdi-chevron-right" aria-hidden="true" />
        </q-item-section>
      </q-item>
    </q-list>
  </div>
</template>

<script setup>
import { DateTime } from 'luxon';
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useStore as useVuex } from 'vuex';

import TasksEmpty from '@/components/user-hub/TasksEmpty.vue';
import { api } from '@/boot/axios';
import { useSSE } from '@/composables/useSSE';
import { useUserHubStore } from '@/stores/userHub';

const router = useRouter();
const vuex = useVuex();
const hub = useUserHubStore();

const tasks = computed(() => hub.tasks);
const loading = computed(() => hub.loadingTasks);

function relative(iso) {
  if (!iso) return '';
  return DateTime.fromISO(iso).toRelative() ?? '';
}

async function refresh() {
  const userKey = vuex.state.session.user?._key;
  if (!userKey) return;
  await hub.refreshTasks(userKey);
}

function openTask(task) {
  router.push({ name: 'taskScreen', params: { taskKey: task._key } });
}

const { subscribe: subscribeTaskSSE } = useSSE('task');

function isAssignedTo(task, userKey) {
  return (task?.assigned_to ?? []).some(
    (a) => a === userKey || a?._key === userKey || a?.user_key === userKey,
  );
}

async function handleTaskEvent(message) {
  let event;
  try {
    event = JSON.parse(message.data);
  } catch {
    return;
  }
  const type = event.event_type || event.notification;
  const taskKey = event.task_key;
  const userKey = vuex.state.session.user?._key;
  if (!taskKey || !userKey) return;

  if (type === 'TASK_COMPLETED' || type === 'TASK_CANCELED') {
    hub.removeTask(taskKey);
    return;
  }
  if (type !== 'TASK_CREATED' && type !== 'TASK_UPDATED' && type !== 'TASK_REOPENED') return;

  try {
    const { data } = await api.get(`/task/${taskKey}`);
    if (isAssignedTo(data, userKey) && data.status === 'open') hub.upsertTask(data);
    else hub.removeTask(taskKey);
  } catch {
    refresh();
  }
}

onMounted(() => {
  subscribeTaskSSE(handleTaskEvent);
});

defineExpose({ refresh, loading });
</script>
