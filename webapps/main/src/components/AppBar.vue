<template>
  <v-app-bar app fixed elevate-on-scroll dense :color="$theme.background">

      <!-- MENU ICON AND WINDOW TITLE -->
      <v-app-bar-nav-icon 
        style="color: rgba(255,255,255,.6);" 
        @click="$emit('showDrawer')"/>
      <h3 class=" display">{{ screen_title }}</h3>

      <!-- USER NAME & BADGE -->
      <h5 class=" display highlight ml-auto">{{ username }}</h5>
      <v-avatar size="28" class="my-auto mr-3 ml-2">
        <v-img :src="avatar_url"></v-img>
      </v-avatar>

      
  </v-app-bar>
</template>

<script>
export default {

  name: 'AppBar',

  data() {
    return {
      show_drawer: false,
    }
  },

  computed: {
    
    screen_title() {
      return this.$store.state.screen_title
    },

    user() {
      return this.$store.state.session.user
    },

    username() {
      return this.user.name + ' ' + this.user.surname
    },

    avatar_name() {
      return (this.user.name + this.user.surname).replace(/\s+/g, '').toLowerCase()
    },

    avatar_url() {
      return "/media/user/" + this.avatar_name + '.jpg'
    }
  },

}
</script>

<style lang="css" scoped>
</style>