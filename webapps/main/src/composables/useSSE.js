import { onBeforeUnmount } from 'vue';
import { api } from '@/boot/axios';

/**
 * Shared SSE manager — ONE multiplexed EventSource per browser tab.
 *
 * Every `useSSE(topic)` registers interest in a topic; the manager keeps a
 * single EventSource open against `/notification/stream?topics=...`, carrying
 * all currently-subscribed topics at once. This is deliberate: opening one
 * connection per topic burns the browser's per-host HTTP/1.1 connection budget
 * (6), so a second tab would exhaust the pool and leave new XHRs stuck pending
 * forever. One connection per tab keeps that budget free.
 *
 * Auth uses a short-lived ticket scoped to the topic SET (POST
 * /notification/ticket with `topics`), not the long-lived JWT in the URL.
 * Events keep their per-topic `event:` name, so each topic's listeners only
 * see their own events.
 */

// topic -> Set<callback>
const topicListeners = new Map();
// topic -> active subscriber count (ref-counted across components)
const topicRefs = new Map();

let source = null;
// Sorted topic set the live EventSource was opened with (',' joined).
let openTopicsKey = '';
let reconcileTimer = null;
// Bumped on every (re)open so a slow ticket mint can detect it was superseded.
let generation = 0;

function activeTopics() {
  return [...topicRefs.keys()].filter((t) => topicRefs.get(t) > 0).sort();
}

function dispatch(topic, event) {
  const listeners = topicListeners.get(topic);
  if (!listeners) return;
  for (const cb of listeners) {
    try {
      cb(event);
    } catch (e) {
      console.error(`[useSSE] ${topic} listener error:`, e);
    }
  }
}

function closeSource() {
  if (source) {
    source.close();
    source = null;
  }
  openTopicsKey = '';
}

async function openStream(topics, myGen) {
  let data;
  try {
    ({ data } = await api.post('/notification/ticket', { topics }));
  } catch (e) {
    console.error('[useSSE] ticket fetch failed for', topics, e);
    return;
  }
  // A newer reconcile/reopen started while we were minting — abandon this one.
  if (myGen !== generation) return;

  const url =
    api.defaults.baseURL +
    '/notification/stream?topics=' +
    encodeURIComponent(topics.join(',')) +
    '&ticket=' +
    encodeURIComponent(data.ticket);

  const es = new EventSource(url, { withCredentials: false });
  for (const topic of topics) {
    es.addEventListener(topic, (event) => dispatch(topic, event));
  }
  es.onerror = () => {
    // The browser gave up reconnecting (ticket likely expired). Re-mint and
    // reopen for whatever the active set is now.
    if (es.readyState === EventSource.CLOSED && myGen === generation) {
      source = null;
      openTopicsKey = '';
      scheduleReconcile();
    }
  };

  source = es;
  openTopicsKey = topics.join(',');
}

function reconcile() {
  reconcileTimer = null;
  const topics = activeTopics();
  const key = topics.join(',');

  // Already streaming exactly this set on a live connection — nothing to do.
  if (key === openTopicsKey && source && source.readyState !== EventSource.CLOSED) {
    return;
  }

  closeSource();
  if (topics.length === 0) return;

  generation += 1;
  openStream(topics, generation).catch(() => {});
}

function scheduleReconcile() {
  // Coalesce the burst of useSSE() calls during a single mount tick into ONE
  // stream open, instead of reopening once per subscribed topic.
  if (reconcileTimer !== null) return;
  reconcileTimer = setTimeout(reconcile, 0);
}

function retain(topic) {
  topicRefs.set(topic, (topicRefs.get(topic) || 0) + 1);
  if (!topicListeners.has(topic)) topicListeners.set(topic, new Set());
  scheduleReconcile();
}

function release(topic, callbacks) {
  const listeners = topicListeners.get(topic);
  if (listeners) {
    for (const cb of callbacks) listeners.delete(cb);
  }
  const next = (topicRefs.get(topic) || 0) - 1;
  if (next <= 0) {
    topicRefs.delete(topic);
    topicListeners.delete(topic);
  } else {
    topicRefs.set(topic, next);
  }
  scheduleReconcile();
}

/**
 * Subscribe a component to a notification topic over the shared stream.
 * Auto-cleans up (and reconciles the shared connection) on unmount.
 *
 * @param {string} topic - The notification topic (e.g. 'production', 'task').
 * @returns {{ subscribe: (cb: (event: MessageEvent) => void) => void }}
 */
export function useSSE(topic) {
  retain(topic);
  const localCallbacks = [];

  function subscribe(cb) {
    topicListeners.get(topic)?.add(cb);
    localCallbacks.push(cb);
  }

  onBeforeUnmount(() => {
    release(topic, localCallbacks);
  });

  return { subscribe };
}
