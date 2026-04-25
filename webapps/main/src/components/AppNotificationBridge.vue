<template>
  <!-- Renderless: no DOM output. Bridge owns the user-scoped SSE lifecycle. -->
</template>

<script setup>
import { computed } from 'vue';
import { useStore } from 'vuex';
import { useSSE } from '@/composables/useSSE';
import { useUserHubStore } from '@/stores/userHub';

// -----------------------------------------------------------------------------
// AppNotificationBridge
//
// Renderless Vue 3 component mounted in MainLayout.vue. Owns the single
// per-user SSE subscription (`user:{user_key}`) and funnels every received
// event into useUserHubStore.pushNotification.
//
// The component is conditionally rendered by the parent layout via
// v-if="user_key", so this <script setup> only runs when a user is logged in.
// Belt-and-braces, we also guard inside with the same check — unit tests
// mount the bridge with a null session to prove the subscribe is skipped.
//
// SSE transport (locked by Plan 02-01 spike + Plan 02-02 backend):
//   - topic argument: "user:" + user_key     (colon, two-level)
//   - useSSE calls POST /notification/ticket with the session JWT in the
//     Authorization header to obtain a 90-second topic-scoped ticket, then
//     opens EventSource at /notification/user:{user_key}?ticket={short-JWT}.
//     The long-lived JWT never appears in a URL — only in the request header
//     of the ticket POST.
//
// Payload shape (Plan 02-02 A3 / D-07):
//   {
//     notification: "TASK_UPDATED",
//     task_key, task_title, assigned_by,
//     timestamp, subtopic, recipient_key
//   }
// Only 5 of those become store fields (id generated client-side; subtopic and
// recipient_key are routing-only, NOT stored — they're filtered out by the
// normalize() whitelist inside useUserHubStore).
// -----------------------------------------------------------------------------

const vuexStore = useStore();
const userHub = useUserHubStore();

const userKey = computed(() => vuexStore.state?.session?.user?._key ?? null);

function generateId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID (e.g. some older
  // happy-dom versions); collision risk is negligible at single-user scale.
  return (
    Date.now().toString(36) +
    '-' +
    Math.random().toString(36).slice(2, 10)
  );
}

function onSSEMessage(evt) {
  let payload;
  try {
    payload = JSON.parse(evt.data);
  } catch (e) {
    // T-02-03-04: tolerate a malformed frame rather than crash the bridge.
    // Log for ops visibility; the event is dropped.
    // eslint-disable-next-line no-console
    console.error('[AppNotificationBridge] parse failed', e);
    return;
  }

  userHub.pushNotification({
    id: generateId(),
    event_type: payload.notification,
    task_key: payload.task_key,
    task_code: payload.task_code,
    assigned_by: payload.assigned_by ?? null,
    ts: payload.timestamp,
    read: false,
  });
}

// Subscribe only when a user is present. The parent already v-if-gates on
// user_key, but login/logout flows can transiently render the layout; this
// inner guard makes the contract local to the bridge and keeps the unit
// test ("does not subscribe when user missing") stable.
if (userKey.value) {
  const { subscribe } = useSSE('user:' + userKey.value);
  subscribe(onSSEMessage);
}
</script>
