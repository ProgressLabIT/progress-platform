import { Notify } from 'quasar';
import { timestamp } from '@/lib/TimeHandling.js';
import store from '@/store';
import { api } from '../boot/axios';

export function sendEvent({ event_type, event_data }) {
  return new Promise((resolve, reject) => {
    const event = {
      event_type,
      user_key: store.state.session.user._key,
      user_session_key: store.state.session.session_key,
      timestamp: timestamp(),
      ...event_data,
    };
    api
      .post('event', event)
      .then((resp) => resolve(resp))
      .catch((err) => {
        Notify.create({
          message: err.response.data.detail.message,
          color: 'theme-red',
          timeout: 0,
          position: 'top',
          actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
        });
        reject(err);
      });
  });
}
