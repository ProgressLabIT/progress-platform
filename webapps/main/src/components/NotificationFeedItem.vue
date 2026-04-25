<template>
  <div
    class="notification-feed-item q-px-md q-py-xs"
    :class="{ 'is-unread': !item.read, 'is-read': item.read }"
    @click="onClick"
  >
    <q-item-label>{{ title }}</q-item-label>
    <q-item-label caption>{{ relative }}</q-item-label>
  </div>
</template>

<script setup>
import { DateTime } from 'luxon';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { useUserHubStore } from '@/stores/userHub';

const props = defineProps({
  item: { type: Object, required: true },
});

const { t, locale } = useI18n();
const router = useRouter();
const userHub = useUserHubStore();

const title = computed(() =>
  t(`notifications.${props.item.event_type}.title`, {
    task: props.item.task_code,
  }),
);

// Relative timestamp (e.g. "2 minutes ago"). Empty string when ts missing or
// luxon returns null (shouldn't happen in practice but the store guarantees
// nothing about ts being well-formed).
const relative = computed(() => {
  if (!props.item.ts) return '';
  return (
    DateTime.fromISO(props.item.ts)
      .setLocale(locale.value)
      .toRelative() ?? ''
  );
});

// D-08: single interaction dispatches both markRead and navigation. markRead
// on a read item is a no-op in the store (Plan 03), so we always call it
// rather than branching — simpler and the store tests already cover idempotency.
function onClick() {
  userHub.markRead(props.item.id);
  router.push({
    name: 'taskScreen',
    params: { taskKey: props.item.task_key },
  });
}
</script>

<style lang="scss" scoped>
.notification-feed-item {
  cursor: pointer;

  &.is-unread {
    border-left: 3px solid var(--theme-blue);
    background: rgba(34, 174, 209, 0.08);

    :deep(.q-item-label:first-child) {
      color: var(--text-high);
    }
  }

  &.is-read {
    :deep(.q-item-label:first-child) {
      color: var(--text-low);
    }
  }

  &:hover {
    background: var(--surface2, #242e31);
  }
}
</style>
