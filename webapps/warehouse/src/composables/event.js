import { timestamp } from '@/lib/TimeHandling.js';
import store from '@/store/index.js';
import { api } from '../boot/axios';


export function sendEvent({ event_type, event_data }) {
  return new Promise((resolve, reject) => {
    const event = {
      event_type,
      user_key: store.state.session.user._key,
      user_session_key: store.state.session.session_key,
      timestamp: timestamp(),
      info: event_data,
    };
    api.post('event', event)
      .then((resp) => {
        // Check for HTTP status code
        if (resp.status >= 200 && resp.status < 300) {
          resolve(resp); // Successful response
        } else {
          reject(new Error(`HTTP Error: ${resp.status}`));
        }
      })
      .catch((err) => reject(err));
  });
}
