<template>
  <v-app style="height: 100vh">
    
    <!-- <template v-if="!session_locked && !is_authenticated">
      <LoginScreen></LoginScreen>
    </template> -->

    <!-- Use v-if to fully remove html from DOM in case of session lock. 
    This avoids access to content by tweaking SessionLock component visibility in the browser inspector -->
    <template v-if="!session_locked">
      <AppBar @showDrawer="show_drawer = true"/> 

      <v-navigation-drawer 
        temporary 
        :color="$theme.surface1"
        app width="400"
        v-model="show_drawer">
        <v-container>
          <v-tabs vertical background-color="transparent">
            
            <v-tab :to="{ name: 'adminPanel'}" class="display mb-2">
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
            </v-tab>
            
          </v-tabs>
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
    </template>
    
    <!-- Pass session_locked as prop instead of computing it locally inside the component since it's already needed for the v-if -->
    <SessionLock v-else v-bind="{session_locked}"></SessionLock>
    
  </v-app>
</template>

<script>
import { DateTime as DT } from 'luxon'

import AppBar from '@/components/AppBar'
import AppFooter from '@/components/AppFooter'
import SessionLock from '@/views/SessionLock'

export default {
  name: 'App',

  components: {
    AppBar,
    AppFooter,
    SessionLock
  },

  data() {
    return {
      show_drawer: false,
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
    

  created() {
    window.onbeforeunload = async (event) => {
      if (this.$route.name != 'login') {
        event.preventDefault()
        this.$store.state.last_interaction = DT.utc().toMillis()
        localStorage.setItem('TEMP_SESSION', JSON.stringify(this.$store.state))
        if (this.is_authenticated) {
          await this.$store.dispatch('logout')
        }
        event.returnValue = 'Sicuro di voler lasciare la pagina?'
      }
      else { event.returnValue = '' }
    }
  },
}
</script>

<style type="text/css" scoped>
.v-tab {
  justify-content: flex-start;
}
</style>
