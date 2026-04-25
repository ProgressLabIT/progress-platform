import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { nextTick, ref } from 'vue';
import { createStore } from 'vuex';

// -----------------------------------------------------------------------------
// Module mocks — hoisted; applied before AppBar.vue is imported in beforeEach.
// -----------------------------------------------------------------------------

vi.mock('@/boot/axios', () => ({ api: { get: vi.fn() } }));

// vue-i18n — locale as a ref, t() echoes the key.
const localeRef = ref('en');
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key) => key,
    locale: localeRef,
    availableLocales: ['en', 'it'],
  }),
}));

// vue-router — minimal stub returning an empty route-like object.
vi.mock('vue-router', () => ({
  useRoute: () => ({ matched: [], name: 'none' }),
}));

// Drawer composables — spies; values not exercised by the badge tests.
const drawerModel = ref(false);
vi.mock('@/composables/drawer', () => ({
  useDrawer: () => ({ drawerModel }),
}));

const rightDrawerToggleSpy = vi.fn();
vi.mock('@/composables/useRightDrawer', () => ({
  useRightDrawer: () => ({
    isOpen: ref(false),
    open: vi.fn(),
    close: vi.fn(),
    toggle: rightDrawerToggleSpy,
  }),
}));

// BaseUserAvatar — stubbed as a lightweight component so we never render the
// real avatar logic and can assert "BaseUserAvatar not modified indirectly".
vi.mock('./BaseUserAvatar.vue', () => ({
  default: {
    name: 'BaseUserAvatar',
    props: ['user', 'size', 'name_first', 'name_class'],
    template:
      '<div class="base-user-avatar-stub" data-testid="base-user-avatar" />',
  },
}));

// -----------------------------------------------------------------------------
// Vuex session store factory
// -----------------------------------------------------------------------------

function makeStore() {
  return createStore({
    state: () => ({
      session: {
        user: { _key: 'u1', name: 'A', surname: 'B' },
      },
    }),
  });
}

// -----------------------------------------------------------------------------
// Global mount config — Quasar stubs
// -----------------------------------------------------------------------------

const globalConfig = {
  stubs: {
    'q-header': { template: '<header class="q-header-stub"><slot/></header>' },
    'q-toolbar': {
      template: '<div class="q-toolbar-stub"><slot/></div>',
    },
    'q-toolbar-title': {
      template: '<div class="q-toolbar-title-stub"><slot/></div>',
    },
    'q-btn': {
      name: 'QBtn',
      template: '<button class="q-btn-stub"><slot/></button>',
      props: ['flat', 'icon', 'padding'],
    },
    // IMPORTANT: QBadge stub must honor v-show via inheritAttrs so the `style`
    // attribute with `display: none` surfaces on the rendered root element —
    // this is what the visibility tests assert.
    'q-badge': {
      name: 'QBadge',
      template:
        '<span class="q-badge-stub" :color="color" :data-floating="String(floating)" :data-rounded="String(rounded)"><slot/></span>',
      props: {
        color: { type: String, default: null },
        floating: { type: Boolean, default: false },
        rounded: { type: Boolean, default: false },
      },
    },
  },
  config: {
    globalProperties: {
      $t: (key) => key,
    },
  },
};

async function mountAppBar() {
  const { default: AppBar } = await import('./AppBar.vue');
  const store = makeStore();
  const wrapper = mount(AppBar, {
    global: { ...globalConfig, plugins: [store] },
  });
  await flushPromises();
  await nextTick();
  return { wrapper, store };
}

function findBadge(wrapper) {
  return wrapper.find('.q-badge-stub');
}

// -----------------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------------

describe('AppBar avatar badge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    drawerModel.value = false;
    localeRef.value = 'en';
    setActivePinia(createPinia());
  });

  afterEach(() => {
    vi.resetModules();
  });

  it('test_badge_hidden_when_no_unread', async () => {
    const { wrapper } = await mountAppBar();
    const badge = findBadge(wrapper);
    expect(badge.exists()).toBe(true);
    // v-show=false surfaces as `display: none` on the style attribute.
    const style = badge.attributes('style') ?? '';
    expect(style.replace(/\s+/g, '')).toContain('display:none');
  });

  it('test_badge_visible_when_unread', async () => {
    const { useUserHubStore } = await import('@/stores/userHub.js');
    const store = useUserHubStore();
    store.pushNotification({
      id: 'n1',
      event_type: 'TASK_UPDATED',
      task_key: 'T1',
      task_code: 'Step 2',
      assigned_by: 'userX',
      ts: '2026-04-17T10:00:00Z',
    });

    const { wrapper } = await mountAppBar();
    const badge = findBadge(wrapper);
    expect(badge.exists()).toBe(true);
    const style = badge.attributes('style') ?? '';
    expect(style.replace(/\s+/g, '')).not.toContain('display:none');
    expect(badge.classes()).toContain('notification-dot');
  });

  it('test_badge_has_floating_rounded_theme_blue', async () => {
    const { wrapper } = await mountAppBar();
    const badge = findBadge(wrapper);
    expect(badge.exists()).toBe(true);
    // Stub proxies props through data-* / color attributes.
    expect(badge.attributes('color')).toBe('theme-blue');
    expect(badge.attributes('data-floating')).toBe('true');
    expect(badge.attributes('data-rounded')).toBe('true');
  });

  it('test_pulse_fires_on_increment', async () => {
    const { wrapper } = await mountAppBar();
    // Initially no pulse class.
    expect(findBadge(wrapper).classes()).not.toContain('notification-pulse');

    const { useUserHubStore } = await import('@/stores/userHub.js');
    const store = useUserHubStore();
    store.pushNotification({
      id: 'n1',
      event_type: 'TASK_UPDATED',
      task_key: 'T1',
      task_code: 'Step 2',
      assigned_by: 'userX',
      ts: '2026-04-17T10:00:00Z',
    });
    await flushPromises();
    await nextTick();

    expect(findBadge(wrapper).classes()).toContain('notification-pulse');
  });

  it('test_pulse_does_not_fire_on_init', async () => {
    // Seed BEFORE mount — simulates the edge case where the store already has
    // unread items on mount (should NOT pulse per Pitfall P7).
    const { useUserHubStore } = await import('@/stores/userHub.js');
    const preStore = useUserHubStore();
    preStore.pushNotification({
      id: 'pre1',
      event_type: 'TASK_UPDATED',
      task_key: 'T0',
      task_code: 'Pre',
      assigned_by: 'x',
      ts: '2026-04-17T09:00:00Z',
    });
    preStore.pushNotification({
      id: 'pre2',
      event_type: 'TASK_UPDATED',
      task_key: 'T0b',
      task_code: 'Pre2',
      assigned_by: 'x',
      ts: '2026-04-17T09:01:00Z',
    });

    const { wrapper } = await mountAppBar();
    await flushPromises();
    await nextTick();

    expect(findBadge(wrapper).classes()).not.toContain('notification-pulse');
  });

  it('test_pulse_does_not_fire_on_decrement', async () => {
    const { useUserHubStore } = await import('@/stores/userHub.js');
    const store = useUserHubStore();
    store.pushNotification({
      id: 'a',
      event_type: 'TASK_UPDATED',
      task_key: 'TA',
      task_code: 'A',
      assigned_by: 'x',
      ts: '2026-04-17T09:00:00Z',
    });
    store.pushNotification({
      id: 'b',
      event_type: 'TASK_UPDATED',
      task_key: 'TB',
      task_code: 'B',
      assigned_by: 'x',
      ts: '2026-04-17T09:01:00Z',
    });

    const { wrapper } = await mountAppBar();
    await flushPromises();
    await nextTick();
    // Init: no pulse even with unread seeded.
    expect(findBadge(wrapper).classes()).not.toContain('notification-pulse');

    // Mark one read — unreadCount 2 → 1 (decrement).
    store.markRead('a');
    await flushPromises();
    await nextTick();

    expect(findBadge(wrapper).classes()).not.toContain('notification-pulse');
  });

  it('test_pulse_clears_after_timeout', async () => {
    vi.useFakeTimers();
    try {
      const { wrapper } = await mountAppBar();

      const { useUserHubStore } = await import('@/stores/userHub.js');
      const store = useUserHubStore();
      store.pushNotification({
        id: 'n1',
        event_type: 'TASK_UPDATED',
        task_key: 'T1',
        task_code: 'Step 2',
        assigned_by: 'x',
        ts: '2026-04-17T10:00:00Z',
      });
      // Flush Vue reactivity without advancing timers.
      await nextTick();
      await nextTick();
      expect(findBadge(wrapper).classes()).toContain('notification-pulse');

      // Advance past 260ms — pulse class must be removed.
      vi.advanceTimersByTime(300);
      await nextTick();
      expect(findBadge(wrapper).classes()).not.toContain('notification-pulse');
    } finally {
      vi.useRealTimers();
    }
  });

  it('test_baseuseravatar_not_modified_indirectly', async () => {
    const { wrapper } = await mountAppBar();
    // Avatar stub still rendered inside the click wrapper alongside the badge.
    const avatar = wrapper.find('[data-testid="base-user-avatar"]');
    expect(avatar.exists()).toBe(true);
    const badge = findBadge(wrapper);
    expect(badge.exists()).toBe(true);
    // Both live inside the same wrapper element that carries the click class.
    const host = wrapper.find('.avatar-badge-host');
    expect(host.exists()).toBe(true);
    expect(host.find('[data-testid="base-user-avatar"]').exists()).toBe(true);
    expect(host.find('.q-badge-stub').exists()).toBe(true);
  });
});
