<template>
  <div
    v-if="!notifications.length"
    class="text-center q-py-lg text-low"
    data-testid="notification-feed-empty"
  >
    <div class="text-body2">{{ $t('notifications.empty.heading') }}</div>
    <div class="text-caption q-mt-xs">{{ $t('notifications.empty.body') }}</div>
  </div>
  <q-scroll-area
    v-else
    :style="{ maxHeight: '240px', height: '240px' }"
    data-testid="notification-feed-scroll"
  >
    <NotificationFeedItem
      v-for="item in notifications"
      :key="item.id"
      :item="item"
    />
  </q-scroll-area>
</template>

<script setup>
import { storeToRefs } from 'pinia';

import NotificationFeedItem from '@/components/NotificationFeedItem.vue';
import { useUserHubStore } from '@/stores/userHub';

// Session-scoped feed (Plan 02-03). notifications is newest-first, capped at
// 100 by the store. We render a flat v-for — no grouping, no virtualisation.
// Max-height 240px inside a QScrollArea scrolls within the feed without
// expanding the enclosing quick panel.
const userHub = useUserHubStore();
const { notifications } = storeToRefs(userHub);
</script>
