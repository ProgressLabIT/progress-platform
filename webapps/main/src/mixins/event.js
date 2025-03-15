import { timestamp } from '@/lib/TimeHandling.js';

export default {
  methods: {
    sendEvent({ event_type, event_data }) {
      return new Promise((resolve) => {
        const session_data = this.$store.state.session;
        const event = {
          event_type,
          user_key: session_data.user._key,
          user_session_key: session_data.session_key,
          timestamp: timestamp(),
          ...event_data,
        };
        this.$api.post('event', event)
          .then((resp) => resolve(resp))
          .catch((err) => {
            this.$q.notify({
              message: err.response.data.detail.message,
              color: 'theme-red',
              timeout: 0,
              position: 'top',
              actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
            });
            throw err;
          });
      });
    },
  },
};
