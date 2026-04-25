import { mount } from '@vue/test-utils';
import { DateTime, Settings } from 'luxon';
import { createPinia, setActivePinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

// -----------------------------------------------------------------------------
// Module mocks — hoisted before component import in beforeEach.
// -----------------------------------------------------------------------------

// vue-i18n: resolve real English strings for the `notifications.*` keys so the
// tests assert rendered user-facing text, not opaque key paths. We implement a
// tiny interpolator to honor `{task}`.
const notifStrings = {
  'notifications.TASK_UPDATED.title': 'Assigned to task {task}',
};
function interp(tpl, params) {
  if (!params) return tpl;
  return tpl.replace(/\{(\w+)\}/g, (_, k) => (k in params ? params[k] : `{${k}}`));
}
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key, params) => {
      const tpl = notifStrings[key];
      if (tpl == null) return key;
      return interp(tpl, params);
    },
    locale: { value: 'en' },
  }),
}));

// vue-router: spy on push
const routerPushSpy = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: routerPushSpy }),
}));

// userHub store: spy on markRead. We mock the module so the component sees a
// predictable, spied-on instance rather than a real Pinia store.
const markReadSpy = vi.fn();
vi.mock('@/stores/userHub', () => ({
  useUserHubStore: () => ({ markRead: markReadSpy }),
}));

// -----------------------------------------------------------------------------
// Global mount config — Quasar stubs (avoid full Quasar plugin install)
// -----------------------------------------------------------------------------

const globalConfig = {
  stubs: {
    'q-item-label': {
      template: '<div class="q-item-label-stub" :class="{ caption }"><slot/></div>',
      props: ['caption'],
    },
  },
};

async function loadComponent() {
  const mod = await import('./NotificationFeedItem.vue');
  return mod.default;
}

function makeItem(overrides = {}) {
  return {
    id: 'n1',
    event_type: 'TASK_UPDATED',
    task_key: 'T1',
    task_code: 'Step 2',
    assigned_by: 'userX',
    ts: '2026-04-17T09:00:00Z',
    read: false,
    ...overrides,
  };
}

// -----------------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------------

describe('NotificationFeedItem', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
    // Pin "now" for deterministic relative timestamps. Pre-compute ms to avoid
    // recursion: DateTime.fromISO internally reads Settings.now.
    const FIXED_NOW_MS = Date.UTC(2026, 3, 17, 9, 5, 0); // 2026-04-17T09:05:00Z
    Settings.now = () => FIXED_NOW_MS;
  });

  afterEach(() => {
    Settings.now = () => Date.now();
  });

  it('test_renders_title_from_i18n_with_task_code', async () => {
    const NotificationFeedItem = await loadComponent();
    const wrapper = mount(NotificationFeedItem, {
      props: { item: makeItem() },
      global: globalConfig,
    });
    expect(wrapper.text()).toContain('Assigned to task Step 2');
  });

  it('test_timestamp_uses_luxon_toRelative', async () => {
    const NotificationFeedItem = await loadComponent();
    const wrapper = mount(NotificationFeedItem, {
      props: { item: makeItem() },
      global: globalConfig,
    });
    // "now" is 5 minutes after item.ts — relative should mention "minute".
    expect(wrapper.text()).toMatch(/minute/);
  });

  it('test_unread_row_has_is_unread_class', async () => {
    const NotificationFeedItem = await loadComponent();
    const wrapper = mount(NotificationFeedItem, {
      props: { item: makeItem({ read: false }) },
      global: globalConfig,
    });
    const root = wrapper.find('.notification-feed-item');
    expect(root.exists()).toBe(true);
    expect(root.classes()).toContain('is-unread');
    expect(root.classes()).not.toContain('is-read');
  });

  it('test_read_row_has_is_read_class', async () => {
    const NotificationFeedItem = await loadComponent();
    const wrapper = mount(NotificationFeedItem, {
      props: { item: makeItem({ read: true }) },
      global: globalConfig,
    });
    const root = wrapper.find('.notification-feed-item');
    expect(root.classes()).toContain('is-read');
    expect(root.classes()).not.toContain('is-unread');
  });

  it('test_click_unread_calls_markRead_and_router_push_once', async () => {
    const NotificationFeedItem = await loadComponent();
    const wrapper = mount(NotificationFeedItem, {
      props: { item: makeItem({ read: false }) },
      global: globalConfig,
    });
    await wrapper.find('.notification-feed-item').trigger('click');
    expect(markReadSpy).toHaveBeenCalledTimes(1);
    expect(markReadSpy).toHaveBeenCalledWith('n1');
    expect(routerPushSpy).toHaveBeenCalledTimes(1);
    expect(routerPushSpy).toHaveBeenCalledWith({
      name: 'taskScreen',
      params: { taskKey: 'T1' },
    });
  });

  it('test_click_read_calls_router_push_but_markRead_is_noop', async () => {
    const NotificationFeedItem = await loadComponent();
    const wrapper = mount(NotificationFeedItem, {
      props: { item: makeItem({ read: true }) },
      global: globalConfig,
    });
    await wrapper.find('.notification-feed-item').trigger('click');
    expect(routerPushSpy).toHaveBeenCalledTimes(1);
    expect(markReadSpy).toHaveBeenCalledTimes(1);
    expect(markReadSpy).toHaveBeenCalledWith('n1');
  });

  it('test_task_code_is_escaped_when_contains_html', async () => {
    const NotificationFeedItem = await loadComponent();
    const hostile = '<img src=x onerror=alert(1)>';
    const wrapper = mount(NotificationFeedItem, {
      props: { item: makeItem({ task_code: hostile }) },
      global: globalConfig,
    });
    // Text contains the literal hostile string (escaped rendering).
    expect(wrapper.text()).toContain(hostile);
    // No actual <img> element was injected into the DOM.
    expect(wrapper.find('img').exists()).toBe(false);
  });
});
