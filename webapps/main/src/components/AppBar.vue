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
            <q-item>
              <q-item-section side>
                <q-icon name="mdi-web" />
              </q-item-section>

              <q-item-section class="flex flex-center">
                <q-btn-toggle
                  v-model="locale"
                  :options="localeOptions"
                  dense
                  padding="xs md"
                  color="theme-grey"
                />
              </q-item-section>
            </q-item>

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

            <q-item>
              <q-item-section side>
                <q-icon name="mdi-file-star" />
              </q-item-section>

              <q-item-section class="flex flex-center">
                <q-select
                  :model-value="homePage"
                  :options="homePageOptions"
                  emit-value
                  map-options
                  :loading="isUpdatingHomePage"
                  :label="$t('preferences.homePage.label')"
                  dense
                  filled
                  class="full-width"
                  @update:model-value="updateHomePage"
                />
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
import { Notify } from 'quasar';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { useStore } from 'vuex';
import { api } from '@/boot/axios';
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

const { t, locale, availableLocales } = useI18n();
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

const localeOptions = availableLocales.map((locale) => ({
  label: locale,
  value: locale,
}));

const homePage = computed({
  get: () => user.value?.home_page || null,
  set: (newHomePage) => store.commit('UPDATE_HOME_PAGE', newHomePage),
});
const homePageOptions = [
  { label: 'Default', value: null },
  { label: 'Settings', value: 'adminPanel' },
  { label: 'Product Library', value: 'libraryRoot' },
  { label: 'Production Monitoring', value: 'productionRoot' },
  { label: 'Job Selection', value: 'operatorRoot' },
  { label: 'Quality', value: 'qualityRoot' },
  { label: 'Reports', value: 'reportRoot' },
];
const isUpdatingHomePage = ref(false);
async function updateHomePage(newHomePage) {
  isUpdatingHomePage.value = true;

  try {
    await api.patch(`/user/${user.value._key}`, { home_page: newHomePage });
    homePage.value = newHomePage;
  } catch (error) {
    console.error(error);
    Notify.create({
      type: 'negative',
      message: t('preferences.homePage.error'),
    });
  } finally {
    isUpdatingHomePage.value = false;
  }
}
</script>
