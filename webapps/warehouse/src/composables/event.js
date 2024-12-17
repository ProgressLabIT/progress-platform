import { timestamp } from '@/lib/TimeHandling.js';
import session from '@/store/session.js';
import { api } from '../boot/axios';


export function sendEvent({ event_type, event_data }) {
  return new Promise((resolve, reject) => {
    const event = {
      event_type,
      user_key: session.state.user._key,
      user_session_key: session.state.session_key,
      timestamp: timestamp(),
      ...event_data,
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
