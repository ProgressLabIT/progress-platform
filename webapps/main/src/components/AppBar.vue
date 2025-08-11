<template>
  <q-header class="header">
    <q-toolbar>
      <q-btn flat icon="mdi-menu" padding="none" @click="drawerModel = true" />

      <q-toolbar-title shrink class="display q-ml-xs q-mr-auto">
        {{ screenTitle }}
      </q-toolbar-title>

      <div class="row items-center cursor-pointer">
        <BaseUserAvatar
          :user="user"
          :size="'28px'"
          name_first
          name_class="app-bar-user-name"
        />

        <q-menu>
          <q-list separator style="min-width: 200px">

            <!-- LANGUAGE -->
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

            <!-- THEME -->
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
                    <q-icon name="mdi-weather-sunny">
                      <q-tooltip>{{ $t('preferences.theme.light') }}</q-tooltip>
                    </q-icon>
                  </template>

                  <template #dark>
                    <q-icon name="mdi-weather-night">
                      <q-tooltip>{{ $t('preferences.theme.dark') }}</q-tooltip>
                    </q-icon>
                  </template>
                </q-btn-toggle>
              </q-item-section>
            </q-item>

            <!-- DISPLAY FONT -->
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

            <!-- HOME PAGE -->
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

            <!-- PRINTER -->
            <q-item>
              <q-item-section side>
                <q-icon name="mdi-printer" />
              </q-item-section>
              <q-item-section class="flex flex-center">
                <q-select
                  :model-value="printer"
                  :options="printerOptions"
                  emit-value
                  map-options
                  :loading="isUpdatingPrinter"
                  :label="$t('preferences.printer.label')"
                  dense
                  filled
                  class="full-width"
                  @update:model-value="updatePrinter"
                />
              </q-item-section>
            </q-item>

            <!-- FULLSCREEN -->
            <q-item clickable @click="$q.fullscreen.toggle()">
              <q-item-section side>
                <q-icon name="mdi-fullscreen" />
              </q-item-section>
              <q-item-section>
                <q-item-label>
                  {{ capitalizeAll($t('fullscreen')) }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-toggle v-model="$q.fullscreen.isActive" />
              </q-item-section>
            </q-item>

            <!-- LOGOUT -->
            <q-item clickable @click="logout">
              <q-item-section side>
                <q-icon name="mdi-logout-variant" />
              </q-item-section>

              <q-item-section>
                <q-item-label>
                  {{ capitalizeAll($t('session.logout')) }}
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
import { cloneDeep, findLast } from 'lodash';
import { Notify , useQuasar } from 'quasar';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';
import { useStore } from 'vuex';
import { capitalize, capitalizeAll } from '@/boot/filters.js';
import { useDrawer } from '@/composables/drawer';
import { useTheme } from '@/composables/theme';
import { useConfigStore } from '@/stores/config';
import BaseUserAvatar from './BaseUserAvatar.vue';

const store = useStore();
const { drawerModel } = useDrawer();
const $q = useQuasar();

const screenTitle = ref('PROGRESS');

const user = computed(() => store.state.session.user);

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
  {
    label: capitalizeAll(t('views.warehouseRoot')),
    value: 'warehouseRoot',
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

const { config } = useConfigStore();

const printer = computed(() => user.value.preferences.printer || null);
const printerOptions = computed(() => {
  return cloneDeep(config.printers).map((printer) => ({
    label: printer.name,
    value: `${printer.host}:${printer.port}`,
  }));
});
const isUpdatingPrinter = ref(false);
async function updatePrinter(newPrinter) {
  isUpdatingPrinter.value = true;

  try {
    await store.dispatch('updatePreferences', { printer: newPrinter });
  } catch (error) {
    console.error(error);
    Notify.create({
      type: 'negative',
      message: t('preferences.printer.error'),
    });
  } finally {
    isUpdatingPrinter.value = false;
  }
}

const displayFont = computed(
  () => user.value.preferences.display_font || 'orbitron',
);
async function updateDisplayFont(newFont) {
  await store.dispatch('updatePreferences', { display_font: newFont });
}
watch(
  displayFont,
  (newFont) => {
    document.body.style.setProperty(
      '--display-font',
      newFont === 'orbitron' ? 'Orbitron' : 'Red Hat Text',
    );
  },
  { immediate: true },
);
</script>
