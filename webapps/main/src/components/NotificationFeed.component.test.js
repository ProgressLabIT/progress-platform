import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

// -----------------------------------------------------------------------------
// Module mocks — hoisted before component import
// -----------------------------------------------------------------------------

vi.mock('@/boot/axios', () => ({ api: { get: vi.fn() } }));

// vue-i18n: resolve the two empty-state keys + section label; pass-through else.
const strings = {
  'notifications.empty.heading': 'No notifications yet',
  'notifications.empty.body': "You'll see task assignments here when they arrive.",
  'notifications.section_label': 'Notifications',
  'notifications.TASK_UPDATED.title': 'Assigned to task {task}',
};
function interp(tpl, params) {
  if (!params) return tpl;
  return tpl.replace(/\{(\w+)\}/g, (_, k) => (k in params ? params[k] : `{${k}}`));
}
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key, params) => {
      const tpl = strings[key];
      return tpl == null ? key : interp(tpl, params);
    },
    locale: { value: 'en' },
  }),
}));

// vue-router — child NotificationFeedItem uses useRouter
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// -----------------------------------------------------------------------------
// Global mount config — Quasar stubs
// -----------------------------------------------------------------------------

const globalConfig = {
  stubs: {
    'q-scroll-area': {
      name: 'QScrollArea',
      template:
        '<div class="q-scroll-area-stub" :style="style" :data-testid="$attrs[\'data-testid\']"><slot/></div>',
      props: ['style'],
      inheritAttrs: false,
    },
    'q-item-label': {
      template: '<div class="q-item-label-stub" :class="{ caption }"><slot/></div>',
      props: ['caption'],
    },
  },
  config: {
    globalProperties: {
      $t: (key) => strings[key] ?? key,
    },
  },
};

async function loadComponent() {
  const mod = await import('./NotificationFeed.vue');
  return mod.default;
}

function makeItem(overrides = {}) {
  return {
    id: overrides.id ?? 'n1',
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

describe('NotificationFeed', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it('test_empty_state_when_no_notifications', async () => {
    const NotificationFeed = await loadComponent();
    const wrapper = mount(NotificationFeed, { global: globalConfig });
    expect(wrapper.text()).toContain('No notifications yet');
    // scroll area must not render in empty state
    expect(wrapper.find('.q-scroll-area-stub').exists()).toBe(false);
  });

  it('test_renders_N_items_in_newest_first_order', async () => {
    const NotificationFeed = await loadComponent();
    const { useUserHubStore } = await import('@/stores/userHub.js');
    const store = useUserHubStore();
    // Push in chronological order; store prepends => newest-first in array.
    // Use task_code to distinguish rendered items — task_code takes
    // precedence over task_key in the title computation.
    store.pushNotification(
      makeItem({ id: 'a', task_key: 'TA', task_code: 'ItemA' }),
    );
    store.pushNotification(
      makeItem({ id: 'b', task_key: 'TB', task_code: 'ItemB' }),
    );
    store.pushNotification(
      makeItem({ id: 'c', task_key: 'TC', task_code: 'ItemC' }),
    );

    const wrapper = mount(NotificationFeed, { global: globalConfig });
    await flushPromises();

    // 3 child items rendered.
    const items = wrapper.findAll('.notification-feed-item');
    expect(items.length).toBe(3);

    // DOM order matches store order (newest-first): c, b, a
    const textOrder = items.map((i) => i.text());
    expect(textOrder[0]).toContain('ItemC');
    expect(textOrder[1]).toContain('ItemB');
    expect(textOrder[2]).toContain('ItemA');
  });

  it('test_scrollarea_max_height_240px', async () => {
    const NotificationFeed = await loadComponent();
    const { useUserHubStore } = await import('@/stores/userHub.js');
    useUserHubStore().pushNotification(makeItem());

    const wrapper = mount(NotificationFeed, { global: globalConfig });
    await flushPromises();

    const scroll = wrapper.find('[data-testid="notification-feed-scroll"]');
    expect(scroll.exists()).toBe(true);
    // Either inline style attribute or :style binding surfaces 240px.
    const styleAttr = scroll.attributes('style') ?? '';
    const raw = wrapper.html();
    expect(styleAttr.includes('240px') || raw.includes('240px')).toBe(true);
  });

  it('test_empty_state_disappears_after_push', async () => {
    const NotificationFeed = await loadComponent();
    const { useUserHubStore } = await import('@/stores/userHub.js');
    const store = useUserHubStore();

    const wrapper = mount(NotificationFeed, { global: globalConfig });
    expect(wrapper.text()).toContain('No notifications yet');

    store.pushNotification(makeItem());
    await flushPromises();

    expect(wrapper.text()).not.toContain('No notifications yet');
    expect(wrapper.findAll('.notification-feed-item').length).toBe(1);
  });
});
