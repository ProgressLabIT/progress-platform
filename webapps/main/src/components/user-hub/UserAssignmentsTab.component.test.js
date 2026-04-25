import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';

vi.mock('@/boot/axios', () => ({ api: { get: vi.fn() } }));
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (k) => k, locale: { value: 'en' } }),
}));
vi.mock('vuex', () => ({
  useStore: () => ({
    state: { session: { user: { _key: 'u1', preferences: {} }, scope: '' } },
    dispatch: vi.fn(),
  }),
}));

const jobsRefreshSpy = vi.fn();
const tasksRefreshSpy = vi.fn();

vi.mock('@/components/user-hub/UserJobsList.vue', () => ({
  default: {
    name: 'UserJobsList',
    template: '<div data-testid="jobs-list"/>',
    setup() {
      const loading = ref(false);
      return { loading, refresh: jobsRefreshSpy };
    },
  },
}));

vi.mock('@/components/user-hub/UserTasksList.vue', () => ({
  default: {
    name: 'UserTasksList',
    template: '<div data-testid="tasks-list"/>',
    setup() {
      const loading = ref(false);
      return { loading, refresh: tasksRefreshSpy };
    },
  },
}));

const globalStubs = {
  stubs: {
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
  },
  config: {
    globalProperties: {
      $capitalize: (s) => (typeof s === 'string' ? s.charAt(0).toUpperCase() + s.slice(1) : s),
      $t: (k) => k,
    },
  },
};

async function mountTab(sub = 'jobs') {
  const { default: UserAssignmentsTab } = await import('./UserAssignmentsTab.vue');
  const wrapper = mount(UserAssignmentsTab, {
    props: { sub },
    global: { plugins: [createPinia()], ...globalStubs },
  });
  await flushPromises();
  return wrapper;
}

describe('UserAssignmentsTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it('renders jobs panel when sub=jobs (AC-04)', async () => {
    const wrapper = await mountTab('jobs');
    expect(wrapper.find('[data-testid="jobs-list"]').exists()).toBe(true);
  });

  it('emits update:sub when clicking tasks tab (AC-06)', async () => {
    const wrapper = await mountTab('jobs');
    await wrapper.find('[data-tab="tasks"]').trigger('click');
    expect(wrapper.emitted('update:sub')?.[0]).toEqual(['tasks']);
  });

  it('renders two sub-tabs (jobs first, then tasks)', async () => {
    const wrapper = await mountTab('jobs');
    const tabs = wrapper.findAll('[data-tab]');
    expect(tabs.length).toBe(2);
    expect(tabs[0].attributes('data-tab')).toBe('jobs');
    expect(tabs[1].attributes('data-tab')).toBe('tasks');
  });

  it('exposes loading and refreshActive via defineExpose (AC-08)', async () => {
    const wrapper = await mountTab('jobs');
    expect(wrapper.vm.loading).toBeDefined();
    expect(wrapper.vm.refreshActive).toBeTypeOf('function');
  });

  it('loading reflects child loading state', async () => {
    const wrapper = await mountTab('jobs');
    expect(wrapper.vm.loading).toBe(false);
  });
});
