<template>
  <div style="height: 100vh">

    <!-- Use v-if to fully remove html from DOM in case of session lock.
    This avoids access to content by tweaking SessionLock component visibility in the browser inspector -->
    <!-- <template v-if="!session_locked"> -->
      <AppBar @showDrawer="show_drawer = true"/>

      <v-navigation-drawer
        temporary
        :color="$theme.surface1"
        app width="400"
        v-model="show_drawer">
        <v-container class="fill-height">
          <v-row class="fill-height">
            <v-col class="d-flex flex-column">

              <v-tabs vertical background-color="transparent">

                <v-tab
                  v-for="tab in tab_routes"
                  :to="{ name: tab }"
                  :key="tab"
                  class="menu display mb-2">
                  {{ $tc(`views.${tab}`) }}
                </v-tab>

                <!-- <v-tab :to="{ name: tab 'adminPanel'}" class="display mb-2">
                  Amminitrazione di sistema
                </v-tab>

                <v-tab :to="{ name: 'libraryRoot'}" class="display mb-2">
                  Libreria prodotti
                </v-tab>

                <v-tab :to="{ name: 'productionRoot'}" class="display mb-2">
                  Monitoraggio produzione
                </v-tab>

                <v-tab :to="{ name: 'operatorRoot'}" class="display">
                  Sessione di lavoro
                </v-tab> -->

              </v-tabs>

              <v-spacer></v-spacer>


              <!-- THEME SELECTION -->
              <v-row class="flex-grow-0 mx-0">
                <v-col cols="auto" class="align-self-center">
                  <span class="display medium">TEMA SCURO</span>
                </v-col>
                <v-spacer></v-spacer>
                <v-switch v-model="dark_mode_on"></v-switch>
              </v-row>

              <!-- LANGUAGE SELECTION -->
              <v-row class="flex-grow-0 mx-0">
                <v-col cols="auto" class="align-self-center">
                  <span class="display medium">{{ $tc('language') }}</span>
                </v-col>
                <v-spacer></v-spacer>
                <v-col>
                  <v-tabs right v-model="locale_index">
                    <v-tab
                      v-for="(lang, i) in locale_list"
                      :key="i">
                      {{ lang }}
                    </v-tab>
                  </v-tabs>
                </v-col>
              </v-row>
            </v-col>
          </v-row>
        </v-container>
      </v-navigation-drawer>

      <v-content class="fill">
        <div class="flex-grow-0 fill">
          <transition name="fade">
            <!-- <keep-alive > -->
              <router-view />
            <!-- </keep-alive> -->
          </transition>
        </div>
      </v-content>

      <AppFooter />

    <!-- Pass session_locked as prop instead of computing it locally inside the component since it's already needed for the v-if -->
    <!-- <SessionLock v-else v-bind="{session_locked}"></SessionLock> -->

  </div>
</template>

<script>
import { DateTime as DT } from 'luxon'
import AppBar from '@/components/AppBar'
import AppFooter from '@/components/AppFooter'
// import SessionLock from '@/views/SessionLock'

export default {
  name: 'App',

  components: {
    AppBar,
    AppFooter,
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

  watch: {
    locale_index(new_locale_index) {
      this.$root.$i18n.locale = this.locale_list[new_locale_index]
      this.$store.state.locale = this.locale_list[new_locale_index]
    },

    dark_mode_on(state) {
      this.$store.dispatch('changeTheme', state)
      this.$vuetify.theme.dark = state
    }
  },

  created() {
    window.addEventListener("beforeunload", async (event) => {
      if (this.$route.name != 'login') {
        event.preventDefault()
        this.$store.state.last_interaction = DT.utc().toMillis()
        localStorage.setItem('TEMP_SESSION', JSON.stringify(this.$store.state))
      }
    })
  },

  beforeMount() {
    let locale = this.$root.$i18n.locale
    const saved_locale = this.$store.state.locale
    if (saved_locale) {
      locale = this.$root.$i18n.locale = saved_locale
    }
    this.locale_index = this.locale_list.findIndex(loc => loc == locale)
  }
}
</script>

<style type="text/css" scoped>
.v-tab.menu {
  justify-content: flex-start;
}
</style>
