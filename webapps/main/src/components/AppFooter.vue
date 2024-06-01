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
      events: NaN,
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
    let eventURL = this.$api.defaults.baseURL + '/notification';
    this.events = new EventSource(eventURL, {
      withCredentials: false,
    });
    this.events.addEventListener('serial-notification', (event) => {
      this.handleMessage(event);
    });
  },

  beforeUnmount() {
    if (this.events) {
      this.events.close();
    }
  },

  methods: {
    getErrorMessage(error_code, default_message) {
      let message = this.$t('traceability.errors.' + error_code);
      if (message) {
        return message;
      }
      return this.$t(default_message);
    },

    handleMessage(message) {
      let event = JSON.parse(message.data);
      if (event.notification === 'ERROR') {
        this.$q.notify({
          message: this.getErrorMessage(event.error_code, event.error),
          color: 'theme-red',
          timeout: 1500,
          position: 'top',
        });
      }
    },
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
