import { sendEvent } from './event.js';
import { api } from '../boot/axios';
import { Notify } from 'quasar';
import store from '@/store';
import { timestamp } from '@/lib/TimeHandling.js';

/**
 * Send multiple events in a single request
 * @param {Array} events - Array of event objects with event_type and event-specific fields
 * @param {Date} eventTimestamp - Optional timestamp to use for all events (defaults to current time)
 * @returns {Promise}
 */
export function sendEventsBulk(events, eventTimestamp = null) {
  return new Promise((resolve, reject) => {
    if (!events || events.length === 0) {
      reject(new Error('No events provided'));
      return;
    }

    // Fallback to single endpoint if only one event
    if (events.length === 1) {
      const event = events[0];
      return sendEvent({
        event_type: event.event_type,
        event_data: event
      }).then(resolve).catch(reject);
    }

    // Extract event_type from first event (all events must be same type)
    const event_type = events[0].event_type;

    // Extract shared data (user, session, timestamp, event_type)
    const shared_data = {
      event_type,
      user_key: store.state.session.user._key,
      user_session_key: store.state.session.session_key,
      timestamp: eventTimestamp || timestamp(),
    };

    // Remove event_type from individual events since it's now in shared_data
    const eventsWithoutType = events.map(e => {
      // eslint-disable-next-line no-unused-vars
      const { event_type, ...rest } = e;
      return rest;
    });

    // Send bulk request
    api
      .post('event/bulk', {
        shared_data,
        events: eventsWithoutType
      })
      .then((resp) => resolve(resp))
      .catch((err) => {
        Notify.create({
          message: err.response?.data?.detail?.message || 'Error sending events',
          color: 'theme-red',
          timeout: 0,
          position: 'top',
          actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
        });
        reject(err);
      });
  });
}

