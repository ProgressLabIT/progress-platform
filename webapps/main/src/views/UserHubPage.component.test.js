import { mount, flushPromises } from '@vue/test-utils';
import { createPinia } from 'pinia';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { createRouter, createMemoryHistory } from 'vue-router';

vi.mock('@/boot/axios', () => ({
  api: { get: vi.fn().mockResolvedValue({ data: [] }) },
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key) => key,
    locale: { value: 'en' },
  }),
}));

vi.mock('vuex', () => ({
  useStore: () => ({
    state: { session: { user: { _key: 'u1', preferences: {} }, scope: '' } },
    dispatch: vi.fn(),
  }),
  createStore: vi.fn(() => ({})),
}));

vi.mock('@/components/user-hub/UserJobsList.vue', () => ({
  default: { name: 'UserJobsList', template: '<div data-testid="jobs-slot"/>' },
}));
vi.mock('@/components/user-hub/UserTasksList.vue', () => ({
  default: { name: 'UserTasksList', template: '<div data-testid="tasks-slot"/>' },
}));
vi.mock('@/components/user-hub/UserPreferencesTab.vue', () => ({
  default: { name: 'UserPreferencesTab', template: '<div data-testid="preferences-slot"/>' },
}));
vi.mock('@/components/FilterDrawer.vue', () => ({
  default: { name: 'FilterDrawer', template: '<div data-testid="filter-drawer"/>' },
}));

const globalStubs = {
  stubs: {
    QPageContainer: { template: '<div class="q-page-container-stub"><slot/></div>' },
    QPage: { template: '<div class="q-page-stub"><slot/></div>' },
    QTabs: {
      props: ['modelValue'],
      emits: ['update:modelValue'],
      template: '<div data-qtabs><slot/></div>',
    },
    QTab: {
      props: ['name', 'label', 'icon'],
      template: '<button :data-tab="name" @click="$parent.$emit(`update:modelValue`, name)">{{ label }}</button>',
    },
    QTabPanels: {
      props: ['modelValue'],
      template: '<div><slot/></div>',
    },
    QTabPanel: {
      props: ['name'],
      template: '<div :data-panel="name" v-show="$parent.modelValue === name"><slot/></div>',
    },
    QSeparator: true,
    QBtn: {
      props: ['icon', 'loading', 'flat', 'round', 'dense'],
      template: '<button :aria-label="$attrs[\'aria-label\']" :data-testid="$attrs[\'data-testid\']"><slot/></button>',
      inheritAttrs: false,
    },
    UserJobsList: { template: '<div data-testid="jobs-slot"/>' },
    UserTasksList: { template: '<div data-testid="tasks-slot"/>' },
    UserPreferencesTab: { template: '<div data-testid="preferences-slot"/>' },
  },
  config: {
    globalProperties: {
      $capitalize: (s) => (typeof s === 'string' ? s.charAt(0).toUpperCase() + s.slice(1) : s),
      $capitalizeAll: (s) => s,
      $t: (key) => key,
    },
  },
};

async function mountPage(query = {}) {
  const { default: UserHubPage } = await import('./UserHubPage.vue');
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/app/user', name: 'userHub', component: UserHubPage, meta: { keepAlive: true } },
      { path: '/', name: 'root', component: { template: '<div/>' } },
    ],
  });
  await router.push({ name: 'userHub', query });
  await router.isReady();
  const replaceSpy = vi.spyOn(router, 'replace');
  const wrapper = mount(UserHubPage, {
    global: {
      plugins: [router, createPinia()],
      ...globalStubs,
    },
  });
  await flushPromises();
  return { wrapper, router, replaceSpy };
}

describe('UserHubPage', () => {
  afterEach(() => {
    vi.resetModules();
  });

  it('renders three tabs: jobs, tasks, preferences', async () => {
    const { wrapper } = await mountPage();
    expect(wrapper.find('[data-tab="jobs"]').exists()).toBe(true);
    expect(wrapper.find('[data-tab="tasks"]').exists()).toBe(true);
    expect(wrapper.find('[data-tab="preferences"]').exists()).toBe(true);
  });

  it('default tab is jobs', async () => {
    const { wrapper } = await mountPage();
    expect(wrapper.find('[data-testid="jobs-slot"]').exists()).toBe(true);
  });

  it('clicking preferences writes tab query via router.replace', async () => {
    const { wrapper, replaceSpy } = await mountPage();
    await wrapper.find('[data-tab="preferences"]').trigger('click');
    await flushPromises();
    expect(replaceSpy).toHaveBeenCalledWith(
      expect.objectContaining({ query: expect.objectContaining({ tab: 'preferences' }) }),
    );
  });

  it('mount with ?tab=preferences shows preferences panel', async () => {
    const { wrapper } = await mountPage({ tab: 'preferences' });
    const panel = wrapper.find('[data-panel="preferences"]');
    expect(panel.exists()).toBe(true);
    expect(panel.isVisible()).toBe(true);
  });

  it('refresh button absent when tab=preferences', async () => {
    const { wrapper } = await mountPage({ tab: 'preferences' });
    expect(wrapper.find('[data-testid="user-hub-refresh"]').exists()).toBe(false);
  });

  it('refresh button present when tab=jobs', async () => {
    const { wrapper } = await mountPage({ tab: 'jobs' });
    const btn = wrapper.find('[data-testid="user-hub-refresh"]');
    expect(btn.exists()).toBe(true);
    expect(btn.attributes('aria-label')).toBeTruthy();
  });

  it('refresh button present when tab=tasks', async () => {
    const { wrapper } = await mountPage({ tab: 'tasks' });
    const btn = wrapper.find('[data-testid="user-hub-refresh"]');
    expect(btn.exists()).toBe(true);
  });

  it('invalid tab value coerces to jobs without router.replace', async () => {
    const { wrapper, replaceSpy } = await mountPage({ tab: 'foo' });
    expect(wrapper.find('[data-testid="jobs-slot"]').exists()).toBe(true);
    expect(replaceSpy).not.toHaveBeenCalled();
  });

  it('refreshes tasks on mount so badge populates before tab is opened', async () => {
    const { api } = await import('@/boot/axios');
    api.get.mockClear();
    await mountPage();
    const taskCall = api.get.mock.calls.find(([url]) => url === '/task');
    expect(taskCall).toBeTruthy();
    expect(taskCall[1]).toEqual({ params: { assigned_to: 'u1' } });
  });

  it('userHub route record has meta.keepAlive true', async () => {
    const fs = await import('node:fs');
    const content = fs.readFileSync('src/router/routes.js', 'utf-8');
    expect(content).toMatch(/name:\s*['"]userHub['"]/);
    expect(content).toMatch(/keepAlive:\s*true/);
  });
});
