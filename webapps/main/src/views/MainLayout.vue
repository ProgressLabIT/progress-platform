<template>
  <q-layout
    view="lHh lpr lFf"
    class="background">

    <!-- Use v-if to fully remove html from DOM in case of session lock.
    This avoids access to content by tweaking SessionLock component visibility in the browser inspector -->
    <!-- <template v-if="!session_locked"> -->
      <AppBar v-if="$q.screen.height > 400"/>

      <q-drawer
        id="menu"
        class="surface2"
        behavior="mobile"
        bordered
        :width="400"
        v-model="show_drawer">
        <div class="column fit q-pa-lg">

          <q-tabs
            class="col-auto"
            vertical switch-indicator>
            <q-route-tab
              v-for="tab in tab_routes"
              :to="{ name: tab }"
              :key="tab"
              active-class="text-theme-blue"
              indicator-color="theme-blue"
              content-class="display">
              {{ $t(`views.${tab}`) }}
            </q-route-tab>
          </q-tabs>

          <q-space />

          <!-- THEME SELECTION -->
          <div class="q-px-sm">
            <div class="row justify-between items-center">
              <div class="display medium">TEMA SCURO</div>
              <q-toggle v-model="dark_mode_on"></q-toggle>
            </div>

            <!-- LANGUAGE SELECTION -->
           <!--  <div class="row justify-between items-center">
              <span class="display medium">{{ $t('language') }}</span>
              <q-tabs right v-model="locale_index">
                <q-tab
                  v-for="(lang, i) in locale_list"
                  :key="i"
                  class="q-ma-none">
                  {{ lang }}
                </q-tab>
              </q-tabs>
            </div> -->
          </div>
        </div>
      </q-drawer>

      <router-view />

      <AppFooter v-if="$q.screen.height > 400"/>

    <!-- Pass session_locked as prop instead of computing it locally inside the component since it's already needed for the v-if -->
    <!-- <SessionLock v-else v-bind="{session_locked}"></SessionLock> -->

  </q-layout>
</template>

<script>
import { useQuasar } from 'quasar'
import { DateTime as DT } from 'luxon'
import AppBar from '@/components/AppBar.vue'
import AppFooter from '@/components/AppFooter.vue'
import drawer from '@/mixins/drawer.js'
// import SessionLock from '@/views/SessionLock'

export default {
  name: 'MainLayout',

  components: {
    AppBar,
    AppFooter
    // SessionLock,
  },

  mixins: [drawer],

  data() {
    return {
      $q: useQuasar(),
      tab_routes: ['adminPanel', 'libraryRoot', 'productionRoot', 'userJobs', 'qualityRoot', 'reportRoot'],
      locale_index: null,
      locale_list: this.$root.$i18n.availableLocales,
      dark_mode_on: true
    }
  },

  computed: {

    user_key() {
      return this.$store.state.session.user._key
    },

    session_locked() {
      return this.$store.state.session.session_locked
    },
  },

  methods: {
    toggleDarkMode(bool) {
      const theme = bool ? 'dark' : 'light'
      document.body.setAttribute('progress-theme', theme)
      // Set theme
      this.$store.dispatch('changeTheme', bool)
      this.$q.dark.set(bool)
    },
  },

  watch: {
    // locale_index(new_locale_index) {
    //   this.$root.$i18n.locale = this.locale_list[new_locale_index]
    //   this.$store.state.locale = this.locale_list[new_locale_index]
    // },
    dark_mode_on(bool) {
      this.toggleDarkMode(bool)
    }
  },

  created() {
    // Set dark mode on
    this.toggleDarkMode(true)
  },
  // beforeMount() {
  //   let locale = this.$root.$i18n.locale
  //   const saved_locale = this.$store.state.locale
  //   if (saved_locale) {
  //     locale = this.$root.$i18n.locale = saved_locale
  //   }
  //   this.locale_index = this.locale_list.findIndex(loc => loc == locale)
  // }
}
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
