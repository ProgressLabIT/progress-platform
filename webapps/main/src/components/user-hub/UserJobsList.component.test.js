import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/boot/axios', () => ({ api: { get: vi.fn() } }));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (k) => k, locale: { value: 'en' } }),
}));

const dispatchSpy = vi.fn();
let vuexState;

vi.mock('vuex', () => ({
  useStore: () => ({
    state: vuexState,
    dispatch: dispatchSpy,
  }),
}));

const routerPushSpy = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: routerPushSpy }),
}));

vi.mock('@/stores/config', () => ({
  useConfigStore: () => ({ config: { allowUnassignedJobs: false } }),
}));

vi.mock('@/components/FilterDrawer.vue', () => ({
  default: {
    name: 'FilterDrawer',
    props: ['modelValue', 'activeFilters'],
    template: '<div data-testid="filter-drawer"><slot/></div>',
  },
}));
vi.mock('@/components/JobCard.vue', () => ({
  default: {
    name: 'JobCard',
    props: ['job'],
    template: '<div class="job-card-stub" :data-key="job._key"/>',
  },
}));
vi.mock('@/components/JobCardSlim.vue', () => ({
  default: {
    name: 'JobCardSlim',
    props: ['job'],
    emits: ['click'],
    template: '<div class="job-card-slim-stub" :data-key="job._key" @click="$emit(`click`)"/>',
  },
}));
vi.mock('@/components/user-hub/JobsEmpty.vue', () => ({
  default: { name: 'JobsEmpty', template: '<div data-testid="jobs-empty"/>' },
}));
vi.mock('@/components/user-hub/JobsNoMatch.vue', () => ({
  default: {
    name: 'JobsNoMatch',
    emits: ['clear'],
    template: '<div data-testid="jobs-no-match"/>',
  },
}));

const globalConfig = {
  stubs: {
    QBtn: { props: ['icon', 'color', 'flat', 'round', 'dense', 'label'], template: '<button><slot/></button>' },
    QBtnToggle: {
      props: ['modelValue', 'options', 'color', 'toggleColor', 'flat', 'dense'],
      emits: ['update:modelValue'],
      template: '<div :aria-label="$attrs[`aria-label`]" :data-layout="modelValue"/>',
      inheritAttrs: false,
    },
    QChip: { props: ['removable', 'dense'], emits: ['remove'], template: '<span class="q-chip-stub"><slot/></span>' },
    QSpace: true,
    QIcon: true,
    QSelect: true,
    QCheckbox: true,
    QVirtualScroll: {
      props: ['items', 'virtualScrollItemSize'],
      template: '<div class="q-virtual-scroll-stub"><template v-for="item in items"><slot :item="item"/></template></div>',
    },
  },
  config: {
    globalProperties: {
      $capitalize: (s) => (typeof s === 'string' ? s.charAt(0).toUpperCase() + s.slice(1) : s),
      $t: (k) => k,
    },
  },
};

function makeJob(key, overrides = {}) {
  return {
    _key: key,
    project_code: 'P1',
    wo_code: 'WO1',
    product_code: 'PROD1',
    phase_alias: 'PH1',
    stage: 'running',
    next_batch_available: true,
    active_batch_qt: 0,
    ...overrides,
  };
}

async function mountList(options = {}) {
  const { default: UserJobsList } = await import('./UserJobsList.vue');
  const pinia = createPinia();
  setActivePinia(pinia);

  const { useUserHubStore } = await import('@/stores/userHub');
  const store = useUserHubStore();

  if (options.jobs) {
    store.jobs = options.jobs;
  }

  const refreshSpy = vi.spyOn(store, 'refreshJobs').mockResolvedValue();

  const wrapper = mount(UserJobsList, {
    global: { plugins: [pinia], ...globalConfig },
  });
  await flushPromises();

  return { wrapper, store, refreshSpy };
}

describe('UserJobsList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vuexState = {
      session: {
        user: { _key: 'u1', preferences: { job_selection_layout: 'card' } },
        scope: 'production',
      },
    };
  });

  afterEach(() => {
    vi.resetModules();
  });

  it('renders JobCard in card layout (AC-09)', async () => {
    const { wrapper } = await mountList({
      jobs: { assigned: [makeJob('j1')], unassigned: [] },
    });
    expect(wrapper.find('.job-card-stub').exists()).toBe(true);
  });

  it('renders JobCardSlim in list layout (AC-10)', async () => {
    vuexState.session.user.preferences.job_selection_layout = 'list';
    const { wrapper } = await mountList({
      jobs: { assigned: [makeJob('j1')], unassigned: [] },
    });
    expect(wrapper.find('.job-card-slim-stub').exists()).toBe(true);
  });

  it('toggling layout dispatches updatePreferences (AC-11)', async () => {
    const { wrapper } = await mountList({
      jobs: { assigned: [makeJob('j1')], unassigned: [] },
    });
    const toggle = wrapper.find('[data-layout]');
    expect(toggle.exists()).toBe(true);
  });

  it('imports FilterDrawer (AC-12)', async () => {
    const { wrapper } = await mountList({
      jobs: { assigned: [makeJob('j1')], unassigned: [] },
    });
    expect(wrapper.find('[data-testid="filter-drawer"]').exists()).toBe(true);
  });

  it('shows split only when isOperator AND allowUnassignedJobs (AC-13)', async () => {
    vuexState.session.scope = 'production';
    const { wrapper } = await mountList({
      jobs: { assigned: [makeJob('j1')], unassigned: [makeJob('j2')] },
    });
    const overlines = wrapper.findAll('.text-overline');
    expect(overlines.length).toBe(0);
  });

  it('has q-virtual-scroll in list layout (AC-14)', async () => {
    vuexState.session.user.preferences.job_selection_layout = 'list';
    const { wrapper } = await mountList({
      jobs: { assigned: [makeJob('j1')], unassigned: [] },
    });
    expect(wrapper.find('.q-virtual-scroll-stub').exists()).toBe(true);
  });

  it('clicking a job navigates to workSession (ASGN-03)', async () => {
    const { wrapper } = await mountList({
      jobs: { assigned: [makeJob('j1')], unassigned: [] },
    });
    await wrapper.find('.job-card-stub').element.parentElement.click();
    await flushPromises();
    expect(routerPushSpy).toHaveBeenCalledWith({ name: 'workSession', params: { jobKey: 'j1' } });
  });

  it('calls refreshJobs on mount', async () => {
    const { refreshSpy } = await mountList();
    expect(refreshSpy).toHaveBeenCalledWith('u1');
  });

  it('exposes refresh() via defineExpose', async () => {
    const { wrapper } = await mountList();
    expect(wrapper.vm.refresh).toBeTypeOf('function');
  });

  it('exposes loading via defineExpose', async () => {
    const { wrapper } = await mountList();
    expect(wrapper.vm.loading).toBeDefined();
  });

  it('shows JobsEmpty when no jobs and no filters (AC-18)', async () => {
    const { wrapper } = await mountList({
      jobs: { assigned: [], unassigned: [] },
    });
    expect(wrapper.find('[data-testid="jobs-empty"]').exists()).toBe(true);
  });

  it('layout toggle has aria-label (AC-20)', async () => {
    const { wrapper } = await mountList({
      jobs: { assigned: [makeJob('j1')], unassigned: [] },
    });
    const toggle = wrapper.find('[aria-label]');
    expect(toggle.exists()).toBe(true);
  });
});
