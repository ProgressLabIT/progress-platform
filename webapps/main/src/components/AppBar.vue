<template>
  <q-header class="header">
    <q-toolbar>
      <q-btn flat icon="mdi-menu" padding="none" @click="drawerModel = true" />

      <q-toolbar-title shrink class="display q-ml-xs q-mr-auto">
        {{ screenTitle }}
      </q-toolbar-title>

      <div class="row items-center cursor-pointer">
        <div class="app-bar-user-name q-mr-sm">{{ username }}</div>
        <q-avatar size="28px">
          <q-img :src="avatarUrl"></q-img>
        </q-avatar>

        <q-menu>
          <q-list separator style="min-width: 200px">
            <q-item
              clickable
              @click="theme = theme === 'dark' ? 'light' : 'dark'"
            >
              <q-item-section side>
                <q-icon
                  :name="
                    theme === 'dark' ? 'mdi-weather-night' : 'mdi-weather-sunny'
                  "
                />
              </q-item-section>

              <q-item-section>
                <q-item-label>
                  {{ capitalizeAll($t('preferences.theme')) }}
                </q-item-label>
              </q-item-section>
            </q-item>

            <q-item clickable @click="logout">
              <q-item-section side>
                <q-icon name="mdi-logout-variant" />
              </q-item-section>

              <q-item-section>
                <q-item-label>
                  {{ capitalizeAll($t('session.close_session')) }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-menu>
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
import { capitalize, capitalizeAll } from '@/boot/filters.js';
import { useDrawer } from '@/composables/drawer';
import { useTheme } from '@/composables/theme';

const store = useStore();
const { drawerModel } = useDrawer();

const screenTitle = ref('PROGRESS');

const user = computed(() => store.state.session.user);
const username = computed(() => {
  if (!user.value) {
    return '';
  }

  const { name, surname } = user.value;
  return `${name} ${surname}`;
});
const avatarUrl = computed(() => {
  if (!user.value) {
    return '';
  }

  const avatarName = username.value.replace(/\s+/g, '').toLowerCase();
  return `/media/user/${avatarName}.jpg`;
});

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

async function logout() {
  const confirm = window.confirm(capitalize(t('session.alerts.close_session')));
  if (confirm) {
    await store.dispatch('logout');
  }
}

const { theme } = useTheme();
</script>
