/**
 * Unit tests for the ticket-based useSSE composable.
 *
 * Strategy:
 *  - Mock `@/boot/axios` so api.post resolves to a fake ticket.
 *  - Mock the global `EventSource` constructor so no real network calls happen.
 *  - Mount a minimal Vue component that calls useSSE() to exercise the
 *    Vue lifecycle hooks (onBeforeUnmount).
 */

import { mount, flushPromises } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent } from 'vue';

// ---------------------------------------------------------------------------
// Mocks — declared before importing the module under test.
// ---------------------------------------------------------------------------

const FAKE_TICKET = 'fake.ticket.jwt';
const FAKE_BASE_URL = 'http://localhost:8080/api';

const mockApiPost = vi.fn(() => Promise.resolve({ data: { ticket: FAKE_TICKET, expires_in: 90 } }));

vi.mock('@/boot/axios', () => ({
  api: {
    post: (...args) => mockApiPost(...args),
    defaults: { baseURL: FAKE_BASE_URL },
  },
}));

// Track EventSource instances created during tests.
let _eventSourceInstances = [];

class FakeEventSource {
  constructor(url, opts) {
    this.url = url;
    this.opts = opts;
    this.readyState = 1; // OPEN
    this._listeners = {};
    this.closed = false;
    _eventSourceInstances.push(this);
  }

  addEventListener(type, handler) {
    this._listeners[type] = handler;
  }

  dispatchEvent(type, event) {
    if (this._listeners[type]) this._listeners[type](event);
  }

  close() {
    this.readyState = 2; // CLOSED
    this.closed = true;
  }
}

FakeEventSource.OPEN = 1;
FakeEventSource.CONNECTING = 0;
FakeEventSource.CLOSED = 2;

beforeEach(() => {
  _eventSourceInstances = [];
  mockApiPost.mockClear();
  vi.stubGlobal('EventSource', FakeEventSource);
});

afterEach(() => {
  vi.unstubAllGlobals();
  // Reset composable module-level `connections` map by re-importing.
  vi.resetModules();
});

// ---------------------------------------------------------------------------
// Helper: mount a component that calls useSSE(topic)
// ---------------------------------------------------------------------------

async function mountWithSSE(topic, subscribe = false) {
  // Re-import after module reset so we get a fresh `connections` Map.
  const { useSSE } = await import('./useSSE.js');

  const callbacks = [];
  const TestComponent = defineComponent({
    setup() {
      const { subscribe: sub } = useSSE(topic);
      if (subscribe) {
        const cb = vi.fn();
        sub(cb);
        callbacks.push(cb);
      }
      return {};
    },
    template: '<div></div>',
  });

  const wrapper = mount(TestComponent, { global: { plugins: [] } });
  return { wrapper, callbacks };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useSSE — ticket fetch', () => {
  it('calls POST /notification/ticket with the topic', async () => {
    await mountWithSSE('production');
    await flushPromises();

    expect(mockApiPost).toHaveBeenCalledOnce();
    expect(mockApiPost).toHaveBeenCalledWith('/notification/ticket', { topic: 'production' });
  });

  it('opens EventSource with ?ticket= query param (no JWT in URL)', async () => {
    await mountWithSSE('task');
    await flushPromises();

    expect(_eventSourceInstances).toHaveLength(1);
    const src = _eventSourceInstances[0];
    expect(src.url).toContain('/notification/task');
    expect(src.url).toContain('?ticket=' + encodeURIComponent(FAKE_TICKET));
    // Long-lived JWT must NOT be in the URL
    expect(src.url).not.toContain('token=');
  });
});

describe('useSSE — ref-counting', () => {
  it('reuses one EventSource for the same topic across two components', async () => {
    const { useSSE } = await import('./useSSE.js');

    const Comp = defineComponent({
      setup() { useSSE('inventory'); return {}; },
      template: '<div></div>',
    });

    mount(Comp, { global: { plugins: [] } });
    mount(Comp, { global: { plugins: [] } });
    await flushPromises();

    // Two mounts of the same topic → still one EventSource, one ticket POST.
    expect(mockApiPost).toHaveBeenCalledOnce();
    expect(_eventSourceInstances).toHaveLength(1);
  });
});

describe('useSSE — message dispatch', () => {
  it('routes messages to subscribed callbacks', async () => {
    const { wrapper, callbacks } = await mountWithSSE('message', true);
    await flushPromises();

    const src = _eventSourceInstances[0];
    const fakeEvent = { data: JSON.stringify({ foo: 'bar' }), event: 'message' };
    src.dispatchEvent('message', fakeEvent);

    expect(callbacks[0]).toHaveBeenCalledWith(fakeEvent);
    wrapper.unmount();
  });
});

describe('useSSE — cleanup on unmount', () => {
  it('closes the EventSource when the last subscriber unmounts', async () => {
    const { wrapper } = await mountWithSSE('serial');
    await flushPromises();

    const src = _eventSourceInstances[0];
    expect(src.closed).toBe(false);

    wrapper.unmount();

    expect(src.closed).toBe(true);
  });

  it('does not close the source while other subscribers still exist', async () => {
    const { useSSE } = await import('./useSSE.js');

    const Comp = defineComponent({
      setup() { useSSE('production'); return {}; },
      template: '<div></div>',
    });

    const w1 = mount(Comp, { global: { plugins: [] } });
    const w2 = mount(Comp, { global: { plugins: [] } });
    await flushPromises();

    const src = _eventSourceInstances[0];
    w1.unmount();
    expect(src.closed).toBe(false);

    w2.unmount();
    expect(src.closed).toBe(true);
  });
});
