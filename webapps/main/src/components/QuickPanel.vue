<template>
  <q-drawer
    v-model="isOpen"
    side="right"
    :width="$q.screen.lt.sm ? undefined : 350"
    behavior="mobile"
    :overlay="true"
    bordered
    class="surface1"
  >
    <BaseConfirmationDialog
      :show="showLogoutConfirm"
      @close="showLogoutConfirm = false"
      @confirm="confirmLogout"
    >
      {{ capitalize(t('session.alerts.close_session')) }}
    </BaseConfirmationDialog>
    <!-- NOTIFICATIONS section (Plan 02-04) -->
    <div class="q-px-md q-pt-md" data-testid="notification-section-header">
      <div class="overline text-low">{{ $t('notifications.section_label') }}</div>
    </div>
    <NotificationFeed />
    <q-separator />
    <q-list separator>
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

      <q-separator />

      <!-- /user link -->
      <q-item clickable :to="{ name: 'userHub' }" @click="close">
        <q-item-section side>
          <q-icon name="mdi-account-circle" />
        </q-item-section>
        <q-item-section>
          <q-item-label>{{ capitalizeAll($t('views.userHub')) }}</q-item-label>
        </q-item-section>
      </q-item>

      <q-separator />

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
  </q-drawer>
</template>

<script setup>
import { onKeyStroke } from '@vueuse/core';
import { Notify } from 'quasar';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStore } from 'vuex';

import { capitalize, capitalizeAll } from '@/boot/filters.js';
import BaseConfirmationDialog from '@/components/BaseConfirmationDialog.vue';
import NotificationFeed from '@/components/NotificationFeed.vue';
import { useTheme } from '@/composables/theme';
import { useRightDrawer } from '@/composables/useRightDrawer';
import { useUserPreferencesOptions } from '@/composables/useUserPreferencesOptions';

const store = useStore();
const { isOpen, close } = useRightDrawer();
const { t, locale, availableLocales } = useI18n();

// Esc key closes the drawer. QDrawer does not handle Escape natively.
onKeyStroke('Escape', () => {
  if (isOpen.value) close();
});

const user = computed(() => store.state.session.user);

// LANGUAGE + PRINTER options from shared composable (AC-17)
const { localeOptions, printerOptions } = useUserPreferencesOptions();

// THEME
const { theme, setTheme } = useTheme();

// DISPLAY FONT
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

// HOME PAGE
const homePage = computed(() => user.value.preferences.home_page || null);
const homePageOptions = computed(() => [
  { label: t('default'), value: null },
  { label: capitalizeAll(t('views.adminPanel')), value: 'adminPanel' },
  { label: capitalizeAll(t('views.libraryRoot')), value: 'libraryRoot' },
  { label: capitalizeAll(t('views.productionRoot')), value: 'productionRoot' },
  { label: capitalizeAll(t('views.operatorRoot')), value: 'operatorRoot' },
  { label: capitalizeAll(t('views.qualityRoot')), value: 'qualityRoot' },
  {
    label: capitalizeAll(t('views.traceabilityRoot')),
    value: 'traceabilityRoot',
  },
  {
    label: capitalizeAll(t('views.taskRoot')),
    value: 'taskRoot',
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

// PRINTER
const printer = computed(() => user.value.preferences.printer || null);
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

// LOGOUT — uses BaseConfirmationDialog because QDrawer's focus trap causes
// Chrome to suppress native window.confirm with "dialog was suppressed
// because this page is not the active tab of the front window".
// Drawer is closed BEFORE dispatching logout (Pitfall P2).
const showLogoutConfirm = ref(false);
function logout() {
  showLogoutConfirm.value = true;
}
async function confirmLogout() {
  showLogoutConfirm.value = false;
  close();
  await store.dispatch('logout');
}

// Expose for tests — Vue 3.4 auto-exposes <script setup> bindings, but defineExpose
// makes the migration-correctness contract explicit for Plan 01-02 Task 2 assertions.
defineExpose({
  updateHomePage,
  updatePrinter,
  updateDisplayFont,
  logout,
  confirmLogout,
  showLogoutConfirm,
});
</script>

<style lang="scss" scoped>
// QuickPanel sits ABOVE FilterDrawer ($z-menu - 1) and BELOW Quasar dialogs ($z-dialog).
// Pattern copied from FilterDrawer.vue; only the $z-index value differs.
// Z-index ordering verified per RESEARCH §Assumptions Log A1:
// Quasar defaults apply: $z-menu=6000, $z-dialog=6000+; ordering valid via DOM/portal.
// (Confirmed no $z-menu / $z-dialog overrides in webapps/main/src/css/* — only FilterDrawer
//  consumes $z-menu, and quasar.variables.scss declares no overrides.)
$z-index: $z-menu;

:deep(.q-drawer--on-top) {
  z-index: $z-index !important;
}

:deep(.q-drawer__backdrop) {
  z-index: $z-index - 1 !important;
}
</style>
