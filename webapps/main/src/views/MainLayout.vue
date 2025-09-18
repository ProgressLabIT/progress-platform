<template>
  <q-layout view="lHh lpr lFf" class="background">
    <!-- Use v-if to fully remove html from DOM in case of session lock.
    This avoids access to content by tweaking SessionLock component visibility in the browser inspector -->
    <!-- <template v-if="!session_locked"> -->
    <AppBar v-if="$q.screen.height > 400" />

    <q-drawer
      id="menu"
      v-model="drawerModel"
      class="surface2"
      behavior="mobile"
      bordered
      :width="400"
    >
      <div class="column fit q-pa-lg">
        <q-tabs class="col-auto" vertical switch-indicator>
          <q-route-tab
            v-for="tab in tab_routes"
            :key="tab"
            :to="{ name: tab }"
            active-class="text-theme-blue"
            indicator-color="theme-blue"
            content-class="display"
          >
            {{ $t(`views.${tab}`) }}
          </q-route-tab>
        </q-tabs>

        <q-space />

        <!-- LANGUAGE SELECTION -->
        <!-- <div class="q-px-sm">
          <div class="row justify-between items-center">
            <span class="display medium">{{ $t('language') }}</span>
            <q-tabs v-model="locale_index" right>
              <q-tab
                v-for="(lang, i) in locale_list"
                :key="i"
                class="q-ma-none"
              >
                {{ lang }}
              </q-tab>
            </q-tabs>
          </div>
        </div> -->
      </div>
    </q-drawer>

    <router-view />

    <AppFooter v-if="$q.screen.height > 400" />

    <!-- Pass session_locked as prop instead of computing it locally inside the component since it's already needed for the v-if -->
    <!-- <SessionLock v-else :session-locked="session_locked" /> -->
  </q-layout>
</template>

<script setup>
import { useQuasar } from 'quasar';
import { computed } from 'vue';
import { useStore } from 'vuex';
import AppBar from '@/components/AppBar.vue';
import AppFooter from '@/components/AppFooter.vue';
import { useDrawer } from '@/composables/drawer';
// import SessionLock from '@/views/SessionLock'

const $q = useQuasar();
const store = useStore();
const { drawerModel } = useDrawer();

const tab_routes = [
  'adminPanel',
  'libraryRoot',
  'productionRoot',
  'userJobs',
  'qualityRoot',
  'traceabilityRoot',
  'taskRoot',
  'warehouseRoot',
  'reportRoot',
];

// locale_index: null,
// locale_list: this.$root.$i18n.availableLocales,

// These computed properties are kept for future use when session lock functionality is enabled
// eslint-disable-next-line no-unused-vars
const user_key = computed(() => {
  return store.state.session.user._key;
});

// eslint-disable-next-line no-unused-vars
const session_locked = computed(() => {
  return store.state.session.session_locked;
});

// watch: {
//   locale_index(new_locale_index) {
//     this.$root.$i18n.locale = this.locale_list[new_locale_index]
//     this.$store.state.locale = this.locale_list[new_locale_index]
//   },
// },

// beforeMount() {
//   let locale = this.$root.$i18n.locale
//   const saved_locale = this.$store.state.locale
//   if (saved_locale) {
//     locale = this.$root.$i18n.locale = saved_locale
//   }
//   this.locale_index = this.locale_list.findIndex(loc => loc == locale)
// }
</script>

<style lang="sass">
#menu .q-tab
  justify-content: left
  padding-left: 15px
  margin-bottom: 8px
  min-height: 30px
  color: var(--text-low)
  .q-tab--active
    color: var(--theme-blue)

.q-drawer__backdrop
  z-index: 9998 !important

.q-drawer--on-top
  z-index:9999
  // border-right: solid 1px grey
</style>
