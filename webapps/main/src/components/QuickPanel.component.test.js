import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';
import { createStore } from 'vuex';

// -----------------------------------------------------------------------------
// Module mocks — hoisted, applied before QuickPanel.vue is imported in beforeEach
// -----------------------------------------------------------------------------

vi.mock('@/boot/axios', () => ({ api: { get: vi.fn() } }));

// Quasar — Notify.create and $q.fullscreen.toggle must be spies
const fullscreenToggleSpy = vi.fn();
vi.mock('quasar', () => ({
  Notify: { create: vi.fn() },
  useQuasar: () => ({
    screen: { lt: { sm: false } },
    fullscreen: { toggle: fullscreenToggleSpy, isActive: false },
  }),
}));

// vue-i18n — locale MUST be a real ref so v-model assignment is reactive
const localeRef = ref('en');
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key) => key,
    locale: localeRef,
    availableLocales: ['en', 'it'],
  }),
}));

// Filters — identity so assertions can match i18n keys directly
vi.mock('@/boot/filters.js', () => ({
  capitalize: (s) => s,
  capitalizeAll: (s) => s,
}));

// Theme composable — spy on setTheme
const setThemeSpy = vi.fn();
vi.mock('@/composables/theme', () => ({
  useTheme: () => ({
    theme: { value: 'light' },
    setTheme: setThemeSpy,
  }),
}));

// Right-drawer composable — spy on close (shared across tests)
const closeSpy = vi.fn();
const isOpenRef = ref(false);
vi.mock('@/composables/useRightDrawer', () => ({
  useRightDrawer: () => ({
    isOpen: isOpenRef,
    open: vi.fn(),
    close: closeSpy,
    toggle: vi.fn(),
  }),
}));

// Config store — reactive printers list shape
vi.mock('@/stores/config', () => ({
  useConfigStore: () => ({
    config: { printers: [{ name: 'p1', host: 'h1', port: 9100 }] },
  }),
}));

// Shared preferences options composable
vi.mock('@/composables/useUserPreferencesOptions', () => ({
  useUserPreferencesOptions: () => ({
    localeOptions: { value: [{ label: 'en', value: 'en' }, { label: 'it', value: 'it' }] },
    themeOptions: [{ slot: 'light', value: 'light' }, { slot: 'dark', value: 'dark' }],
    displayFontOptions: [{ slot: 'orbitron', value: 'orbitron' }, { slot: 'red-hat-display', value: 'red-hat-display' }],
    printerOptions: { value: [{ label: 'p1', value: 'h1:9100' }] },
  }),
}));

// -----------------------------------------------------------------------------
// Vuex store factory
// -----------------------------------------------------------------------------

function makeStore() {
  return createStore({
    state: () => ({
      session: {
        user: {
          preferences: {
            locale: 'en',
            theme: 'light',
            display_font: 'orbitron',
            home_page: null,
            printer: null,
          },
        },
      },
    }),
    actions: {
      updatePreferences: vi.fn().mockResolvedValue(undefined),
      logout: vi.fn().mockResolvedValue(undefined),
    },
  });
}

// -----------------------------------------------------------------------------
// Global mount config — Quasar stubs
// -----------------------------------------------------------------------------

const globalConfig = {
  stubs: {
    'q-drawer': {
      name: 'QDrawer',
      template: '<div class="q-drawer-stub"><slot/></div>',
    },
    'q-list': { template: '<ul class="q-list-stub"><slot/></ul>' },
    'q-item': {
      name: 'QItem',
      template:
        '<li class="q-item-stub" @click="$emit(\'click\', $event)"><slot/></li>',
      props: ['clickable', 'to'],
      emits: ['click'],
    },
    'q-item-section': { template: '<div class="q-item-section-stub"><slot/></div>' },
    'q-item-label': { template: '<div class="q-item-label-stub"><slot/></div>' },
    'q-icon': { props: ['name'], template: '<i :class="`q-icon-stub ${name}`" />' },
    'q-separator': { template: '<hr class="q-separator-stub" />' },
    'q-tooltip': { template: '<span class="q-tooltip-stub"><slot/></span>' },
    // NotificationFeed is mounted from within QuickPanel (Plan 02-04). We stub
    // it to keep this test focused on QuickPanel composition, not feed rendering.
    NotificationFeed: {
      name: 'NotificationFeed',
      template: '<div class="notification-feed-stub" data-testid="notification-feed-stub" />',
    },
    'q-btn-toggle': {
      name: 'QBtnToggle',
      template: '<button class="q-btn-toggle-stub">toggle</button>',
      props: ['modelValue', 'options'],
      emits: ['update:modelValue'],
    },
    'q-select': {
      name: 'QSelect',
      template: '<select class="q-select-stub"></select>',
      props: ['modelValue', 'options', 'loading'],
      emits: ['update:modelValue'],
    },
    'q-toggle': {
      name: 'QToggle',
      template: '<input type="checkbox" class="q-toggle-stub" />',
      props: ['modelValue'],
      emits: ['update:modelValue'],
    },
  },
  config: {
    globalProperties: {
      $t: (key) => key,
      $q: {
        screen: { lt: { sm: false } },
        fullscreen: { toggle: fullscreenToggleSpy, isActive: false },
      },
    },
  },
};

// -----------------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------------

describe('QuickPanel', () => {
  let store;
  let QuickPanel;

  beforeEach(async () => {
    vi.clearAllMocks();
    localeRef.value = 'en';
    isOpenRef.value = false;
    setActivePinia(createPinia());
    QuickPanel = (await import('./QuickPanel.vue')).default;
  });

  it('mounts without error', () => {
    store = makeStore();
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    expect(wrapper.find('.q-drawer-stub').exists()).toBe(true);
  });

  it('updateHomePage dispatches updatePreferences with home_page payload (PANEL-03)', async () => {
    const dispatch = vi.fn().mockResolvedValue(undefined);
    store = makeStore();
    store.dispatch = dispatch;
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    await wrapper.vm.updateHomePage('adminPanel');
    expect(dispatch).toHaveBeenCalledWith('updatePreferences', {
      home_page: 'adminPanel',
    });
  });

  it('updatePrinter error path calls Notify.create with negative (PANEL-03)', async () => {
    const { Notify } = await import('quasar');
    const dispatch = vi.fn().mockRejectedValue(new Error('boom'));
    store = makeStore();
    store.dispatch = dispatch;
    // Silence the expected console.error noise
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    await wrapper.vm.updatePrinter('h:9100');
    expect(Notify.create).toHaveBeenCalledWith(
      expect.objectContaining({ type: 'negative' }),
    );
    consoleErrorSpy.mockRestore();
  });

  it('updateDisplayFont dispatches updatePreferences with display_font (PANEL-03)', async () => {
    const dispatch = vi.fn().mockResolvedValue(undefined);
    store = makeStore();
    store.dispatch = dispatch;
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    await wrapper.vm.updateDisplayFont('red-hat-display');
    expect(dispatch).toHaveBeenCalledWith('updatePreferences', {
      display_font: 'red-hat-display',
    });
  });

  it('language toggle dispatches updatePreferences or mutates locale (PANEL-03)', async () => {
    const dispatch = vi.fn().mockResolvedValue(undefined);
    store = makeStore();
    store.dispatch = dispatch;
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    const toggles = wrapper.findAllComponents({ name: 'QBtnToggle' });
    expect(toggles.length).toBeGreaterThanOrEqual(1);
    // First toggle in UI-SPEC item order is language (v-model="locale")
    await toggles[0].vm.$emit('update:modelValue', 'it');
    await wrapper.vm.$nextTick();

    const sawLocaleDispatch = dispatch.mock.calls.some(
      ([action, payload]) =>
        action === 'updatePreferences' && payload && 'locale' in payload,
    );
    const sawLocaleMutation = localeRef.value === 'it';
    expect(sawLocaleDispatch || sawLocaleMutation).toBe(true);
  });

  it('theme toggle calls setTheme (PANEL-03)', async () => {
    store = makeStore();
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    const toggles = wrapper.findAllComponents({ name: 'QBtnToggle' });
    expect(toggles.length).toBeGreaterThanOrEqual(2);
    // Second toggle in UI-SPEC item order is theme (@update:model-value="setTheme")
    await toggles[1].vm.$emit('update:modelValue', 'dark');
    expect(setThemeSpy).toHaveBeenCalledWith('dark');
  });

  it('fullscreen item click calls $q.fullscreen.toggle (PANEL-03)', async () => {
    store = makeStore();
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    const items = wrapper.findAllComponents({ name: 'QItem' });
    for (const item of items) {
      await item.trigger('click');
    }
    expect(fullscreenToggleSpy).toHaveBeenCalled();
  });

  it('logout() opens the confirmation dialog without dispatching (PANEL-04)', async () => {
    const dispatch = vi.fn().mockResolvedValue(undefined);
    store = makeStore();
    store.dispatch = dispatch;
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    wrapper.vm.logout();
    expect(wrapper.vm.showLogoutConfirm).toBe(true);
    expect(closeSpy).not.toHaveBeenCalled();
    expect(dispatch).not.toHaveBeenCalledWith('logout');
  });

  it('confirmLogout closes drawer BEFORE dispatching logout (PANEL-04 — Pitfall P2)', async () => {
    const dispatch = vi.fn().mockResolvedValue(undefined);
    store = makeStore();
    store.dispatch = dispatch;
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    wrapper.vm.logout();
    await wrapper.vm.confirmLogout();
    expect(wrapper.vm.showLogoutConfirm).toBe(false);
    expect(closeSpy).toHaveBeenCalled();
    expect(dispatch).toHaveBeenCalledWith('logout');
    expect(closeSpy.mock.invocationCallOrder[0]).toBeLessThan(
      dispatch.mock.invocationCallOrder[0],
    );
  });

  it('dialog close (cancel) does NOT dispatch logout or close drawer (PANEL-04)', async () => {
    const dispatch = vi.fn().mockResolvedValue(undefined);
    store = makeStore();
    store.dispatch = dispatch;
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    wrapper.vm.logout();
    expect(wrapper.vm.showLogoutConfirm).toBe(true);
    // Simulate user cancelling via BaseConfirmationDialog @close
    wrapper.vm.showLogoutConfirm = false;
    expect(closeSpy).not.toHaveBeenCalled();
    expect(dispatch).not.toHaveBeenCalledWith('logout');
  });

  it('renders /user link targeting route name userHub (PANEL-05)', () => {
    store = makeStore();
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    const items = wrapper.findAllComponents({ name: 'QItem' });
    const hasUserHubLink = items.some((c) => {
      const to = c.props('to');
      return to && typeof to === 'object' && to.name === 'userHub';
    });
    expect(hasUserHubLink).toBe(true);
  });

  it('preference changes do NOT close the drawer (D-11 regression)', async () => {
    const dispatch = vi.fn().mockResolvedValue(undefined);
    store = makeStore();
    store.dispatch = dispatch;
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    await wrapper.vm.updateHomePage('adminPanel');
    await wrapper.vm.updatePrinter('h:9100');
    await wrapper.vm.updateDisplayFont('red-hat-display');
    expect(closeSpy).not.toHaveBeenCalled();
  });

  // --- Plan 02-04: Notification feed integration ----------------------------

  it('quickpanel contains notification section header + <NotificationFeed /> (PANEL-02)', () => {
    store = makeStore();
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    // The NotificationFeed stub is mounted.
    expect(wrapper.find('[data-testid="notification-feed-stub"]').exists()).toBe(
      true,
    );
    // Section overline text ("notifications.section_label") is rendered via
    // $t, which the global stub echoes back verbatim.
    expect(wrapper.text()).toContain('notifications.section_label');
  });

  it('notification feed is placed ABOVE the preferences list (PANEL-02 / DOM order)', () => {
    store = makeStore();
    const wrapper = mount(QuickPanel, {
      global: { ...globalConfig, plugins: [store] },
    });
    const html = wrapper.html();
    const feedIdx = html.indexOf('notification-feed-stub');
    const langIdx = html.indexOf('mdi-web');
    expect(feedIdx).toBeGreaterThan(-1);
    expect(langIdx).toBeGreaterThan(-1);
    expect(feedIdx).toBeLessThan(langIdx);
  });
});
