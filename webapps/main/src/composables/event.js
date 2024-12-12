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
    api
      .post('event', event)
      .then((resp) => resolve(resp))
      .catch((err) => reject(err));
  });
}
