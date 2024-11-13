<template>
  <q-layout view="lHh lpr lFf" class="background" @click="closeFooter">
    <AppBar v-if="$q.screen.height > 400" />
    <router-view />
    <AppFooter v-if="$q.screen.height > 400" />
  </q-layout>
</template>

<script>
import { useQuasar } from 'quasar';
import AppBar from 'src/components/AppBar.vue';
import AppFooter from 'src/components/AppFooter.vue';

export default {
  name: 'MainLayout',

  components: {
    AppBar,
    AppFooter,
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
    };
  },

  methods: {
    closeFooter() {
      this.$bus.emit('close-footer');
    },
  },
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
