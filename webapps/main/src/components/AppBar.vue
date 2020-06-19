<template>
  <v-app-bar app fixed elevate-on-scroll dense :color="$theme.background">

      <!-- MENU ICON AND WINDOW TITLE -->
      <v-app-bar-nav-icon 
      ref="icon"
        style="color: rgba(255,255,255,.6);" 
        @click="$emit('showDrawer')"/>
      <h3 class=" display">{{ screen_title }}</h3>

      <!-- USER NAME & BADGE -->
      <h5 class=" display highlight ml-auto">{{ username }}</h5>
      <v-hover  v-slot:default="{ hover }">
        <v-avatar size="28" class="my-auto ml-2">
          <v-img v-if="!hover" :src="avatar_url"></v-img>
          <v-icon v-else 
            @click="logout">
            mdi-exit-to-app
          </v-icon>
        </v-avatar>
      </v-hover>
      
  </v-app-bar>
</template>

<script>
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

  },

  methods: {
    async logout() {
      const confirm = window.confirm('Sicuro di voler terminare la sessione?')
      if (confirm) {
        await this.$store.dispatch('logout')
      }
    }
  },

  watch: {
    $route (to) {
      const route_with_title = to.matched.slice().reverse().find( r => r.meta.screen_title )
      if (route_with_title) {
        this.screen_title = route_with_title.meta.screen_title || 'PROGRESS'
      }
    }
  }

}
</script>

<style lang="css" scoped>
</style>