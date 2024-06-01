<template>
  <q-footer class="footer footer-text">
    <div class="row q-pa-sm display smaller">
      <div class="col">{{ config.companyName }}</div>
      <div style="width: 70px">{{ time }}</div>
      <div class="col text-right">{{ date }}</div>
    </div>
  </q-footer>
</template>

<script>
import { DateTime } from 'luxon';
import { useConfigStore } from '../stores/config';

export default {
  name: 'AppFooter',

  setup() {
    const { config } = useConfigStore();
    return {
      config,
    };
  },

  data() {
    return {
      now: 0,
    };
  },

  computed: {
    time() {
      return this.now
        .setLocale(this.$i18n.locale)
        .toLocaleString(DateTime.TIME_WITH_SECONDS);
    },
    date() {
      return this.now
        .setLocale(this.$i18n.locale)
        .toLocaleString(DateTime.DATE_HUGE);
    },
  },

  created() {
    this.now = DateTime.local();
    setInterval(() => {
      this.now = DateTime.local();
    }, 1000);
  },
};
</script>

<style lang="css" scoped>
.material-icons.smaller {
  font-size: 0.9em;
  vertical-align: bottom;
}

.footer-text {
  color: rgba(255, 255, 255, 0.6);
}
</style>
