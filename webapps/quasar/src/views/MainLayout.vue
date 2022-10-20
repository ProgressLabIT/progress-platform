<template>
  <q-layout view="lHh lpR lFf" style="height: 100vh" class="background">

    <!-- Use v-if to fully remove html from DOM in case of session lock.
    This avoids access to content by tweaking SessionLock component visibility in the browser inspector -->
    <!-- <template v-if="!session_locked"> -->
      <AppBar @showDrawer="show_drawer = true"/>

      <q-drawer
        class="surface1"
        behavior="mobile"
        width="400"
        v-model="show_drawer">
        <div class="column fit q-pa-lg">

          <q-tabs
            class="col"
            vertical switch-indicator>
            <q-route-tab
              v-for="tab in tab_routes"
              :to="{ name: tab }"
              :key="tab"
              class="menu display mb-2">
              {{ $t(`views.${tab}`) }}
            </q-route-tab>
          </q-tabs>

          <q-space />

          <!-- THEME SELECTION -->
          <div class="row justify-between">
            <div class="display medium">TEMA SCURO</div>
            <q-toggle v-model="dark_mode_on"></q-toggle>
          </div>

          <!-- LANGUAGE SELECTION -->
          <div class="row justify-between">
            <span class="display medium">{{ $t('language') }}</span>
            <v-tabs right v-model="locale_index">
              <v-tab
                v-for="(lang, i) in locale_list"
                :key="i">
                {{ lang }}
              </v-tab>
            </v-tabs>
          </div>
        </div>
      </q-drawer>

      <q-page-container>
        <transition name="fade">
          <router-view />
        </transition>
      </q-page-container>

      <AppFooter />

    <!-- Pass session_locked as prop instead of computing it locally inside the component since it's already needed for the v-if -->
    <!-- <SessionLock v-else v-bind="{session_locked}"></SessionLock> -->

  </q-layout>
</template>

<script>
import { DateTime as DT } from 'luxon'
import AppBar from '@/components/AppBar.vue'
import AppFooter from '@/components/AppFooter.vue'
// import SessionLock from '@/views/SessionLock'

export default {
  name: 'App',

  components: {
    AppBar,
    AppFooter
    // SessionLock,
  },

  data() {
    return {
      show_drawer: false,
      tab_routes: ['adminPanel', 'libraryRoot', 'productionRoot', 'userJobs'],
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
    }
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
    // window.addEventListener("beforeunload", async (event) => {
    //   if (this.$route.name != 'login') {
    //     event.preventDefault()
    //     this.$store.state.last_interaction = DT.utc().toMillis()
    //     localStorage.setItem('TEMP_SESSION', JSON.stringify(this.$store.state))
    //   }
    // })
    this.toggleDarkMode(true)
  }

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

<style type="text/css" scoped>

</style>
