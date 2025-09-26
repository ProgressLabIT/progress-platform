import { Notify } from 'quasar';
import { timestamp } from '@/lib/TimeHandling.js';
import store from '@/store';
import { useTaskStore } from '@/stores/task.js';
import { api } from '../boot/axios';


export async function sendEvent({ event_type, event_data }) {
  try {
    let finalEventData = { ...event_data };

    // Get active task if exists and automatically add task context
    const taskStore = useTaskStore();
    const activeTask = taskStore.getActiveTask;
    if (activeTask) {
      finalEventData.context_type = 'task'
      finalEventData.context_key = activeTask._key;
    }

    const event = {
      event_type,
      user_key: store.state.session.user._key,
      user_session_key: store.state.session.session_key,
      timestamp: timestamp(),
      ...finalEventData,
    };

    const response = await api.post('event', event);
    return response;

  } catch (err) {
    Notify.create({
      message: err.response?.data?.detail?.message || 'An error occurred while sending the event',
      color: 'theme-red',
      timeout: 0,
      position: 'top',
      actions: [{ label: 'CLOSE', color: 'white', handler: () => {} }],
    });
    throw err;
  }
}

