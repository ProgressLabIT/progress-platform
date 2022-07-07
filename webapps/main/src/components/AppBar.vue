<template>
  <v-app-bar app fixed elevate-on-scroll dense class="grey--text text--lighten-2">

      <!-- MENU ICON AND WINDOW TITLE -->
      <v-icon @click="$emit('showDrawer')" class="grey--text text--lighten-2">mdi-menu</v-icon>
      <h3 class="display ml-3 mr-auto">{{ screen_title }}</h3>

      <!-- USER NAME & BADGE -->
      <v-hover v-slot:default="{ hover }">
        <div class="d-flex align-center justify-end">
          <h5 class="display">{{ username }}</h5>
          <v-avatar size="28" class="my-auto ml-2">
            <v-img v-if="!hover" :src="avatar_url"></v-img>
            <v-icon v-else class="grey--text text--lighten-2"
              @click="logout">
              mdi-exit-to-app
            </v-icon>
          </v-avatar>
        </div>
      </v-hover>
      
  </v-app-bar>
</template>

<script>
import { capitalize as c } from '@/lib/filters.js'
export default {

  name: 'AppBar',

  data() {
    return {
      show_drawer: false,
      screen_title: 'Progress'
    }
  },

  computed: {
    
    session_data() {
      return this.$store.state.session
    },

    user() {
      return this.session_data.user
    },

    username() {
      return this.user ? this.user.name + ' ' + this.user.surname : ''
    },

    avatar_name() {
      return this.user ? (this.user.name + this.user.surname).replace(/\s+/g, '').toLowerCase() : ''
    },

    avatar_url() {
      return this.user ? "/media/user/" + this.avatar_name + '.jpg' : ''
    },

    locale() {
      return this.$root.$i18n.locale
    }

  },

  methods: {
    async logout() {
      const confirm = window.confirm(c(this.$tc('session.alerts.close_session')))
      if (confirm) {
        await this.$store.dispatch('logout')
      }
    },

    update_screen_title(route) {
      const route_with_title = route.matched.slice().reverse().find( r => r.meta.screen_title )
      if (route_with_title) {
        const new_screen_title = this.$tc(`views.${route_with_title.name}`) || 'PROGRESS'
        this.screen_title = new_screen_title
      }
    }
  },

  created() {
    this.update_screen_title(this.$route)
  },

  watch: {
    $route (to) {
      this.update_screen_title(to)
    },
    locale() {
      this.update_screen_title(this.$route)
    }
  }

}
</script>

<style lang="css" scoped>
</style>
