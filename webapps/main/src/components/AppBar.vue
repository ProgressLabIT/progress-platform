<template>
  <q-header class="header">
    <q-toolbar>
      <q-btn flat icon="mdi-menu" padding="none" @click="drawerModel = true" />

      <q-toolbar-title shrink class="display q-ml-xs q-mr-auto">
        {{ screenTitle }}
      </q-toolbar-title>

      <div
        class="row items-center cursor-pointer avatar-badge-host"
        @click="toggleRightDrawer"
      >
        <BaseUserAvatar
          :user="user"
          :size="'28px'"
          name_first
          name_class="app-bar-user-name"
        />
        <q-badge
          v-show="userHub.hasUnread"
          :class="{ 'notification-pulse': pulseActive }"
          color="theme-blue"
          floating
          rounded
        />
        <!-- preference subtree removed — moved to QuickPanel.vue (Plan 02) -->
      </div>
    </q-toolbar>
  </q-header>
</template>

<script setup>
import { findLast } from 'lodash';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { useStore } from 'vuex';
import { useDrawer } from '@/composables/drawer';
import { useRightDrawer } from '@/composables/useRightDrawer';
import { useUserHubStore } from '@/stores/userHub';
import BaseUserAvatar from './BaseUserAvatar.vue';

const store = useStore();
const { drawerModel } = useDrawer();
const { toggle: toggleRightDrawer } = useRightDrawer();

const screenTitle = ref('PROGRESS');

const user = computed(() => store.state.session.user);

const userHub = useUserHubStore();
const pulseActive = ref(false);

// Pulse on strict increment only. `prev` is undefined on Vue's first watcher
// invocation even without { immediate: true } — the nullish-coalesce guards
// the Pitfall P7 edge case (seeded-store-on-mount must not pulse).
watch(
  () => userHub.unreadCount,
  (n, prev) => {
    if (n > (prev ?? 0)) {
      pulseActive.value = true;
      setTimeout(() => {
        pulseActive.value = false;
      }, 260);
    }
  },
);

const { t, locale } = useI18n();
const route = useRoute();
watch(
  [locale, route],
  () => {
    const routeWithTitle = findLast(
      route.matched,
      ({ meta }) => !!meta.screen_title,
    );

    if (routeWithTitle) {
      screenTitle.value = t(`views.${routeWithTitle.name}`) || 'PROGRESS';
    }
  },
  { immediate: true },
);
</script>

<style lang="scss" scoped>
.avatar-badge-host {
  position: relative;
  display: inline-flex;
}

@keyframes notification-pulse {
  0%   { transform: scale(1);   opacity: 1; }
  50%  { transform: scale(1.6); opacity: 0.7; }
  100% { transform: scale(1);   opacity: 1; }
}

.notification-pulse {
  animation: notification-pulse 250ms ease-out forwards;
}
</style>
