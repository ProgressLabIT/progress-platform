import { onBeforeUnmount } from 'vue';
import { api } from '@/boot/axios';

const connections = new Map();

async function mintAndOpen(topic, entry) {
  let data;
  try {
    ({ data } = await api.post('/notification/ticket', { topic }));
  } catch (e) {
    console.error(`[useSSE] ticket fetch failed for "${topic}":`, e);
    return;
  }
  if (entry.closed) return;

  const base = api.defaults.baseURL + '/notification/' + topic;
  const url = base + '?ticket=' + encodeURIComponent(data.ticket);
  const source = new EventSource(url, { withCredentials: false });

  source.addEventListener(topic, (event) => {
    for (const cb of entry.listeners) {
      try { cb(event); } catch (e) { console.error(`[useSSE] ${topic} listener error:`, e); }
    }
  });

  source.onerror = () => {
    // If the browser has given up on reconnecting (CLOSED state), the ticket
    // may have expired. Fetch a fresh ticket and reopen the connection.
    if (source.readyState === EventSource.CLOSED && !entry.closed) {
      entry.source = null;
      mintAndOpen(topic, entry).catch(() => {});
    }
  };

  entry.source = source;
}

function getOrCreate(topic) {
  let entry = connections.get(topic);
  if (entry) {
    entry.refCount++;
    return entry;
  }

  entry = { source: null, listeners: new Set(), refCount: 1, closed: false };
  connections.set(topic, entry);
  mintAndOpen(topic, entry).catch(() => {});
  return entry;
}

function release(topic) {
  const entry = connections.get(topic);
  if (!entry) return;
  entry.refCount--;
  if (entry.refCount <= 0) {
    entry.closed = true;
    if (entry.source) entry.source.close();
    entry.listeners.clear();
    connections.delete(topic);
  }
}

/**
 * Composable for shared SSE subscriptions.
 * Maintains one EventSource per topic (ref-counted across components).
 * Auth is handled via a short-lived ticket (POST /notification/ticket)
 * rather than passing the long-lived JWT in the URL.
 * Auto-cleans up when the component unmounts.
 *
 * @param {string} topic - e.g. 'inventory'
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
