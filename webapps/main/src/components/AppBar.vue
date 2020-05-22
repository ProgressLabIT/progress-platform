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
            @click="$router.push({name: 'login'})">
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
      sections: {
        product: 'Libreria prodotti',
        production: 'monitoraggio produzione',
        'select-job': 'Selezione lavoro',
        worksession: 'sessione di lavoro',
        'admin': 'pannello amministrazione'
      }
    }
  },

  computed: {
    
    screen_title() {
      // return this.$store.state.screen_title
      const section = this.$route.path.split('/')[1]
      return this.sections[section]
    },

    user() {
      return this.$store.state.traceability.user
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