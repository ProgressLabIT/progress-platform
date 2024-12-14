<template>
  <q-header class="header">
    <q-toolbar>
      <!--<q-btn flat icon="mdi-menu" padding="none" @click="drawerModel = true" />-->

      <q-breadcrumbs separator=">" class="text-low uppercase" active-color="text-low">
        <!-- <q-breadcrumbs-el>
          <q-icon name="mdi-home" size="xs"/>
        </q-breadcrumbs-el> -->

        <q-breadcrumbs-el
          v-for="route in breadcrumb"
          :key="route.name"
          :label="$t(route.meta.title)"
          :to="{ name: route.name }"
        />
      </q-breadcrumbs>


      <q-space></q-space>


      <BaseUserAvatar :user="user" :show_name="false" id="avatar" style="cursor: pointer"/>

      <q-menu target="#avatar">
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

            <q-item>
              <q-item-section side>
                <q-icon name="mdi-palette-swatch" />
              </q-item-section>

              <q-item-section class="flex flex-center">
                <q-btn-toggle
                  :model-value="theme"
                  :options="[
                    { slot: 'light', value: 'light' },
                    { slot: 'dark', value: 'dark' },
                  ]"
                  dense
                  no-caps
                  padding="xs md"
                  color="theme-grey"
                  @update:model-value="setTheme"
                >
                  <template #light>
                    <q-icon name="mdi-weather-sunny" />
                  </template>

                  <template #dark>
                    <q-icon name="mdi-weather-night" />
                  </template>
                </q-btn-toggle>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section side>
                <q-icon name="mdi-format-font" />
              </q-item-section>

              <q-item-section class="flex flex-center">
                <q-btn-toggle
                  :model-value="displayFont"
                  :options="[
                    { slot: 'orbitron', value: 'orbitron' },
                    {
                      slot: 'red-hat-display',
                      value: 'red-hat-display',
                    },
                  ]"
                  dense
                  no-caps
                  padding="xs md"
                  color="theme-grey"
                  @update:model-value="updateDisplayFont"
                >
                  <template #orbitron>
                    <q-icon name="mdi-orbit">
                      <q-tooltip>Orbitron</q-tooltip>
                    </q-icon>
                  </template>

                  <template #red-hat-display>
                    <q-icon name="mdi-redhat">
                      <q-tooltip>Red Hat Display</q-tooltip>
                    </q-icon>
                  </template>
                </q-btn-toggle>
              </q-item-section>
            </q-item>

            <q-item>
              <q-item-section side>
                <q-icon name="mdi-home" />
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
                  {{ capitalizeAll($t('logout')) }}
                </q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-menu>

    </q-toolbar>
  </q-header>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { useStore } from 'vuex';
import { capitalize, capitalizeAll } from 'src/boot/filters.js';
import { useTheme } from 'src/composables/theme';
import BaseUserAvatar from './BaseUserAvatar.vue';

const store = useStore();

const user = computed(() => store.state.session.user);

const { t, locale, availableLocales } = useI18n();
const route = useRoute();

const breadcrumb = computed(() => {
  return route.matched.filter(({ meta }) => meta.title);
});

async function logout() {
  const confirm = window.confirm(capitalize(t('session.alerts.close_session')));
  if (confirm) {
    await store.dispatch('logout');
  }
}

const { theme, setTheme } = useTheme();

const localeOptions = availableLocales.map((locale) => ({
  label: locale,
  value: locale,
}));

const homePage = computed(() => user.value.preferences.home_page || null);
const homePageOptions = computed(() => [
  { label: t('default'), value: null },
  { label: capitalizeAll(t('views.adminPanel')), value: 'adminPanel' },
  { label: capitalizeAll(t('views.libraryRoot')), value: 'libraryRoot' },
  { label: capitalizeAll(t('views.productionRoot')), value: 'productionRoot' },
  { label: capitalizeAll(t('views.userJobs')), value: 'operatorRoot' },
  { label: capitalizeAll(t('views.qualityRoot')), value: 'qualityRoot' },
  {
    label: capitalizeAll(t('views.traceabilityRoot')),
    value: 'traceabilityRoot',
  },
  { label: capitalizeAll(t('views.reportRoot')), value: 'reportRoot' },
]);
const isUpdatingHomePage = ref(false);
async function updateHomePage(newHomePage) {
  isUpdatingHomePage.value = true;

  try {
    await store.dispatch('updatePreferences', { home_page: newHomePage });
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

const displayFont = computed(
  () => user.value.preferences.display_font || 'orbitron'
);
async function updateDisplayFont(newFont) {
  await store.dispatch('updatePreferences', { display_font: newFont });
}
watch(
  displayFont,
  (newFont) => {
    document.body.style.setProperty(
      '--display-font',
      newFont === 'orbitron' ? 'Orbitron' : 'Red Hat Text'
    );
  },
  { immediate: true }
);
</script>
