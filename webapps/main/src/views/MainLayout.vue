<template>
  <q-layout view="lHh lpr lFf" class="background">
    <!-- Use v-if to fully remove html from DOM in case of session lock.
    This avoids access to content by tweaking SessionLock component visibility in the browser inspector -->
    <!-- <template v-if="!session_locked"> -->
    <AppBar v-if="$q.screen.height > 400" />
    <router-view />
    <AppFooter v-if="$q.screen.height > 400" />
  </q-layout>
</template>

<script>
import { useQuasar } from 'quasar';
import AppBar from '@/components/AppBar.vue';
import AppFooter from '@/components/AppFooter.vue';
import { useDrawer } from '@/composables/drawer';
// import SessionLock from '@/views/SessionLock'

export default {
  name: 'MainLayout',

  components: {
    AppBar,
    AppFooter,
    // SessionLock,
  },

  setup() {
    const { drawerModel } = useDrawer();

    return {
      drawerModel,
    };
  },

  data() {
    return {
      $q: useQuasar(),
      tab_routes: [
        'adminPanel',
        'libraryRoot',
        'productionRoot',
        'userJobs',
        'qualityRoot',
        'traceabilityRoot',
        'reportRoot',
      ],
      // locale_index: null,
      // locale_list: this.$root.$i18n.availableLocales,
    };
  },

  computed: {
    user_key() {
      return this.$store.state.session.user._key;
    },

    session_locked() {
      return this.$store.state.session.session_locked;
    },
  },

  watch: {
    // locale_index(new_locale_index) {
    //   this.$root.$i18n.locale = this.locale_list[new_locale_index]
    //   this.$store.state.locale = this.locale_list[new_locale_index]
    // },
  },

  // beforeMount() {
  //   let locale = this.$root.$i18n.locale
  //   const saved_locale = this.$store.state.locale
  //   if (saved_locale) {
  //     locale = this.$root.$i18n.locale = saved_locale
  //   }
  //   this.locale_index = this.locale_list.findIndex(loc => loc == locale)
  // }
};
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
