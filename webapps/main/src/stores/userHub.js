import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { DateTime } from 'luxon';

import { api } from '@/boot/axios';

// ---------------------------------------------------------------------------
// useUserHubStore — session-scoped notification feed (Plan 02-03)
//
// Session-only state: no persistence. Populated by AppNotificationBridge.vue
// subscribing to `user:{user_key}` over SSE; consumed by NotificationFeed
// (Plan 04) and the avatar badge (Plan 05).
//
// Contract is frozen here — downstream plans must not mutate or extend the
// public surface below without a new plan.
// ---------------------------------------------------------------------------

// D-09 / PITFALLS P6: feed size cap. Oldest item evicts on push when length
// would exceed this value. Bounds memory over long sessions.
const FEED_CAP = 100;

// Whitelist of the 7 fields the store accepts from an incoming notification
// payload. Unknown keys are silently dropped. This is the T-02-03-01 mitigation
// (tampering / XSS): attacker-influenced fields cannot leak into UI state via
// the SSE payload, and vue-i18n auto-escapes the known fields when rendered
// by Plan 04's feed.
const ALLOWED_KEYS = [
  'id',
  'event_type',
  'task_key',
  'task_code',
  'assigned_by',
  'ts',
  'read',
];

function normalize(item) {
  const out = {};
  for (const k of ALLOWED_KEYS) {
    out[k] = item[k];
  }
  // read defaults to false — incoming SSE payloads never carry a server-side
  // read flag in v1 (read state is session-local per D-11).
  if (typeof out.read !== 'boolean') out.read = false;
  return out;
}

export const useUserHubStore = defineStore('userHub', () => {
  const notifications = ref([]);

  const unreadCount = computed(
    () => notifications.value.filter((n) => !n.read).length,
  );
  const hasUnread = computed(() => unreadCount.value > 0);

  function pushNotification(item) {
    notifications.value.unshift(normalize(item));
    if (notifications.value.length > FEED_CAP) {
      // Truncate in place from the tail — oldest items are at the end after
      // unshift, so length = FEED_CAP drops exactly the overflow.
      notifications.value.length = FEED_CAP;
    }
  }

  function markRead(id) {
    const n = notifications.value.find((x) => x.id === id);
    if (n && !n.read) n.read = true;
  }

  const jobs = ref({ assigned: [], unassigned: [] });
  const tasks = ref([]);
  const loadingJobs = ref(false);
  const loadingTasks = ref(false);
  const lastLoadedAt = ref({ jobs: null, tasks: null });

  async function refreshJobs(userKey) {
    loadingJobs.value = true;
    try {
      const { data } = await api.get('/job-assignment', { params: { user_key: userKey } });
      const rawAssigned = data?.detail?.assigned_jobs_by_operator?.[0]?.assigned_jobs ?? [];
      const rawUnassigned = data?.detail?.unassigned_jobs ?? [];
      // JobCard reads `job.assigned` to pick the avatar icon. The /job-assignment
      // payload only buckets by section, so stamp the flag onto each item here
      // (legacy UserJobs.vue did the same on the consumer side).
      jobs.value = {
        assigned: rawAssigned.map((j) => ({ ...j, assigned: true })),
        unassigned: rawUnassigned.map((j) => ({ ...j, assigned: false })),
      };
      lastLoadedAt.value = { ...lastLoadedAt.value, jobs: new Date().toISOString() };
    } finally {
      loadingJobs.value = false;
    }
  }

  async function refreshTasks(userKey) {
    loadingTasks.value = true;
    try {
      const { data } = await api.get('/task', { params: { assigned_to: userKey } });
      tasks.value = data.map(withOverdue) ?? [];
      lastLoadedAt.value = { ...lastLoadedAt.value, tasks: new Date().toISOString() };
    } finally {
      loadingTasks.value = false;
    }
  }

  function withOverdue(task) {
    return {
      ...task,
      is_overdue: task.due_by && DateTime.fromISO(task.due_by).diffNow().as('days') < 0,
    };
  }

  // Targeted mutations driven by SSE events. Mirror the splice-in-place pattern
  // used by `UPDATE_SINGLE_JOB` in the legacy Vuex store (store/job.js) so Vue
  // reactivity picks up the change without rebuilding the array.
  function applyJobUpdate(jobData, userKey) {
    if (!jobData?._key) return;
    const key = jobData._key;
    const assignedIdx = jobs.value.assigned.findIndex((j) => j._key === key);
    const unassignedIdx = jobs.value.unassigned.findIndex((j) => j._key === key);

    if (jobData.stage === 'closed') {
      if (assignedIdx !== -1) jobs.value.assigned.splice(assignedIdx, 1);
      if (unassignedIdx !== -1) jobs.value.unassigned.splice(unassignedIdx, 1);
      return;
    }

    const target = jobData.assigned_to === userKey
      ? 'assigned'
      : jobData.assigned_to == null
        ? 'unassigned'
        : null;

    if (target === null) {
      if (assignedIdx !== -1) jobs.value.assigned.splice(assignedIdx, 1);
      if (unassignedIdx !== -1) jobs.value.unassigned.splice(unassignedIdx, 1);
      return;
    }

    const bucket = jobs.value[target];
    const otherBucket = target === 'assigned' ? jobs.value.unassigned : jobs.value.assigned;
    const inTargetIdx = target === 'assigned' ? assignedIdx : unassignedIdx;
    const inOtherIdx = target === 'assigned' ? unassignedIdx : assignedIdx;
    const assignedFlag = target === 'assigned';

    if (inTargetIdx !== -1) {
      bucket.splice(inTargetIdx, 1, { ...bucket[inTargetIdx], ...jobData, assigned: assignedFlag });
      return;
    }
    if (inOtherIdx !== -1) otherBucket.splice(inOtherIdx, 1);
    bucket.push({ ...jobData, assigned: assignedFlag });
  }

  function removeJob(jobKey) {
    jobs.value.assigned = jobs.value.assigned.filter((j) => j._key !== jobKey);
    jobs.value.unassigned = jobs.value.unassigned.filter((j) => j._key !== jobKey);
  }

  function upsertTask(task) {
    if (!task?._key) return;
    const enriched = withOverdue(task);
    const idx = tasks.value.findIndex((t) => t._key === task._key);
    if (idx !== -1) tasks.value.splice(idx, 1, enriched);
    else tasks.value.push(enriched);
  }

  function removeTask(taskKey) {
    tasks.value = tasks.value.filter((t) => t._key !== taskKey);
  }

  async function loadAssignments(userKey) {
    await Promise.all([refreshJobs(userKey), refreshTasks(userKey)]);
  }

  async function refreshAssignments(userKey) {
    return loadAssignments(userKey);
  }

  function reset() {
    notifications.value = [];
    jobs.value = { assigned: [], unassigned: [] };
    tasks.value = [];
    loadingJobs.value = false;
    loadingTasks.value = false;
    lastLoadedAt.value = { jobs: null, tasks: null };
  }

  return {
    notifications,
    unreadCount,
    hasUnread,
    pushNotification,
    markRead,
    reset,
    jobs,
    tasks,
    loadingJobs,
    loadingTasks,
    lastLoadedAt,
    loadAssignments,
    refreshAssignments,
    refreshJobs,
    refreshTasks,
    applyJobUpdate,
    removeJob,
    upsertTask,
    removeTask,
  };
});
