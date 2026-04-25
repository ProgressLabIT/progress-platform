import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createStore } from 'vuex';

// -----------------------------------------------------------------------------
// Module-level mocks. vi.mock is hoisted, so these are registered before the
// component is imported in beforeEach().
// -----------------------------------------------------------------------------

const subscribeSpy = vi.fn();
const useSSESpy = vi.fn(() => ({ subscribe: subscribeSpy }));

vi.mock('@/composables/useSSE', () => ({
  useSSE: (...args) => useSSESpy(...args),
}));

// -----------------------------------------------------------------------------
// Vuex store helper — mirrors the real session shape used by MainLayout.vue.
// -----------------------------------------------------------------------------

function makeStore(userKey) {
  return createStore({
    state: () => ({
      session: {
        user: userKey ? { _key: userKey } : null,
        auth_token: 'fake-jwt-for-tests',
      },
    }),
    getters: {
      getToken: (state) => state.session.auth_token,
    },
  });
}

async function mountBridge(userKey) {
  const { default: AppNotificationBridge } = await import(
    './AppNotificationBridge.vue'
  );
  const store = makeStore(userKey);
  const wrapper = mount(AppNotificationBridge, {
    global: { plugins: [store] },
  });
  await flushPromises();
  return { wrapper, store };
}

describe('AppNotificationBridge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
    // Default useSSE impl — individual tests may override.
    useSSESpy.mockImplementation(() => ({ subscribe: subscribeSpy }));
  });

  afterEach(() => {
    vi.resetModules();
  });

  it('test_renders_empty_template — no DOM output (renderless)', async () => {
    const { wrapper } = await mountBridge('abc');
    // Renderless component: innerHTML should be empty or whitespace-only
    // (Vue may render a single comment placeholder <!----> for the template comment).
    const html = wrapper.html().replace(/<!--.*?-->/g, '').trim();
    expect(html).toBe('');
  });

  it('test_subscribes_on_mount_with_user_key — useSSE("user:abc") called once', async () => {
    await mountBridge('abc');
    expect(useSSESpy).toHaveBeenCalledTimes(1);
    expect(useSSESpy).toHaveBeenCalledWith('user:abc');
    expect(subscribeSpy).toHaveBeenCalledTimes(1);
    expect(typeof subscribeSpy.mock.calls[0][0]).toBe('function');
  });

  it('test_does_not_subscribe_when_user_missing', async () => {
    await mountBridge(null);
    expect(useSSESpy).not.toHaveBeenCalled();
    expect(subscribeSpy).not.toHaveBeenCalled();
  });

  it('test_event_payload_pushes_to_store — valid JSON is normalized into userHub', async () => {
    await mountBridge('abc');
    const callback = subscribeSpy.mock.calls[0][0];

    // Simulate the SSE event emitted by the backend (Plan 02-02 A3/D-07 shape).
    callback({
      data: JSON.stringify({
        notification: 'TASK_UPDATED',
        task_key: 'T1',
        task_code: 'Step 2',
        assigned_by: 'userX',
        timestamp: '2026-04-17T10:00:00Z',
        subtopic: 'user:abc',
        recipient_key: 'abc',
      }),
    });

    // Read from the active pinia store the bridge uses.
    const { useUserHubStore } = await import('@/stores/userHub.js');
    const store = useUserHubStore();

    expect(store.notifications.length).toBe(1);
    const item = store.notifications[0];
    expect(item.event_type).toBe('TASK_UPDATED');
    expect(item.task_key).toBe('T1');
    expect(item.task_code).toBe('Step 2');
    expect(item.assigned_by).toBe('userX');
    expect(item.ts).toBe('2026-04-17T10:00:00Z');
    expect(item.read).toBe(false);
    expect(typeof item.id).toBe('string');
    expect(item.id.length).toBeGreaterThan(0);
    // subtopic / recipient_key must NOT leak into the store (T-02-03-01).
    expect(item).not.toHaveProperty('subtopic');
    expect(item).not.toHaveProperty('recipient_key');
  });

  it('test_malformed_json_is_ignored_not_thrown (T-02-03-04)', async () => {
    const consoleErrSpy = vi
      .spyOn(console, 'error')
      .mockImplementation(() => {});
    await mountBridge('abc');
    const callback = subscribeSpy.mock.calls[0][0];

    // Must not throw.
    expect(() => callback({ data: 'not-json {{{' })).not.toThrow();

    const { useUserHubStore } = await import('@/stores/userHub.js');
    const store = useUserHubStore();
    expect(store.notifications.length).toBe(0);

    consoleErrSpy.mockRestore();
  });

  it('test_id_is_unique_across_events', async () => {
    await mountBridge('abc');
    const callback = subscribeSpy.mock.calls[0][0];

    for (let i = 0; i < 3; i++) {
      callback({
        data: JSON.stringify({
          notification: 'TASK_UPDATED',
          task_key: 'T' + i,
          task_code: 'Step ' + i,
          assigned_by: 'userA',
          timestamp: '2026-04-17T10:00:0' + i + 'Z',
        }),
      });
    }

    const { useUserHubStore } = await import('@/stores/userHub.js');
    const store = useUserHubStore();
    expect(store.notifications.length).toBe(3);
    const ids = store.notifications.map((n) => n.id);
    expect(new Set(ids).size).toBe(3);
  });
});
