import { onBeforeUnmount } from 'vue';
import { api } from '@/boot/axios';

const connections = new Map();

function getOrCreate(topic) {
  let entry = connections.get(topic);
  if (entry) {
    entry.refCount++;
    return entry;
  }

  const url = api.defaults.baseURL + '/notification/' + topic;
  const source = new EventSource(url, { withCredentials: false });
  const listeners = new Set();

  source.addEventListener(topic, (event) => {
    for (const cb of listeners) {
      try { cb(event); } catch (e) { console.error(`[useSSE] ${topic} listener error:`, e); }
    }
  });

  source.onerror = () => {};

  entry = { source, listeners, refCount: 1 };
  connections.set(topic, entry);
  return entry;
}

function release(topic) {
  const entry = connections.get(topic);
  if (!entry) return;
  entry.refCount--;
  if (entry.refCount <= 0) {
    entry.source.close();
    entry.listeners.clear();
    connections.delete(topic);
  }
}

/**
 * Composable for shared SSE subscriptions.
 * Maintains one EventSource per topic (ref-counted across components).
 * Auto-cleans up when the component unmounts.
 *
 * @param {string} topic - The notification topic (e.g. 'global-notification')
 * @returns {{ subscribe: (cb: (event: MessageEvent) => void) => void }}
 */
export function useSSE(topic) {
  const entry = getOrCreate(topic);
  const localCallbacks = [];

  function subscribe(cb) {
    entry.listeners.add(cb);
    localCallbacks.push(cb);
  }

  onBeforeUnmount(() => {
    for (const cb of localCallbacks) {
      entry.listeners.delete(cb);
    }
    release(topic);
  });

  return { subscribe };
}
