<template>
  <q-header class="header">
    <q-toolbar>
      <q-btn flat icon="mdi-menu" padding="none" @click="show_drawer = true">
      </q-btn>
      <q-toolbar-title shrink class="display q-ml-xs q-mr-auto">{{
        screen_title
      }}</q-toolbar-title>

      <div
        class="row items-center pointer"
        @mouseover="show_logout = true"
        @mouseleave="show_logout = false"
      >
        <div class="app-bar-user-name q-mr-sm">{{ username }}</div>
        <q-avatar size="28px">
          <q-img v-if="!show_logout" :src="avatar_url"></q-img>
          <q-icon v-else name="mdi-exit-to-app" size="sm" @click="logout" />
        </q-avatar>
      </div>
    </q-toolbar>
  </q-header>
</template>

<script>
import { capitalize as c } from '@/boot/filters.js';
import drawer from '@/mixins/drawer.js';

export default {
  name: 'AppBar',

  mixins: [drawer],

  data() {
    return {
      show_logout: false,
      screen_title: 'Progress',
    };
  },

  computed: {
    session_data() {
      return this.$store.state.session;
    },

    user() {
      return this.session_data.user;
    },

    username() {
      return this.user ? this.user.name + ' ' + this.user.surname : '';
    },

    avatar_name() {
      return this.user
        ? (this.user.name + this.user.surname).replace(/\s+/g, '').toLowerCase()
        : '';
    },

    avatar_url() {
      return this.user ? '/media/user/' + this.avatar_name + '.jpg' : '';
    },

    locale() {
      return this.$root.$i18n.locale;
    },
  },

  watch: {
    $route(to) {
      this.update_screen_title(to);
    },
    locale() {
      this.update_screen_title(this.$route);
    },
  },

  created() {
    this.update_screen_title(this.$route);
  },

  methods: {
    async logout() {
      const confirm = window.confirm(
        c(this.$t('session.alerts.close_session')),
      );
      if (confirm) {
        await this.$store.dispatch('logout');
      }
    },

    update_screen_title(route) {
      const route_with_title = route.matched
        .slice()
        .reverse()
        .find((r) => r.meta.screen_title);
      if (route_with_title) {
        const new_screen_title =
          this.$t(`views.${route_with_title.name}`) || 'PROGRESS';
        this.screen_title = new_screen_title;
      }
    },
  },
};
</script>
