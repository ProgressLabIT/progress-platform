import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/boot/axios', () => ({ api: { get: vi.fn() } }));
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (k) => k, locale: { value: 'en' } }),
}));

const dispatchSpy = vi.fn();
vi.mock('vuex', () => ({
  useStore: () => ({
    state: { session: { user: { _key: 'u1', preferences: {} }, scope: '' } },
    dispatch: dispatchSpy,
  }),
}));

const routerPushSpy = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: routerPushSpy }),
}));

vi.mock('@/components/user-hub/TasksEmpty.vue', () => ({
  default: { name: 'TasksEmpty', template: '<div data-testid="tasks-empty"/>' },
}));

const globalConfig = {
  stubs: {
    QList: { template: '<div class="q-list-stub"><slot/></div>' },
    QItem: {
      props: ['clickable'],
      template: '<div class="q-item-stub" @click="$emit(`click`)"><slot/></div>',
    },
    QItemSection: { template: '<div class="q-item-section-stub"><slot/></div>' },
    QItemLabel: {
      props: ['lines', 'caption'],
      template: '<div class="q-item-label-stub" :class="$attrs.class"><slot/></div>',
      inheritAttrs: false,
    },
    QIcon: {
      props: ['name', 'color'],
      template: '<i :data-icon="name" :data-color="color"/>',
    },
    QInnerLoading: { props: ['showing'], template: '<div v-if="showing" data-testid="inner-loading"><slot/></div>' },
    QSpinnerDots: true,
  },
  config: {
    globalProperties: {
      $capitalize: (s) => s,
      $t: (k) => k,
    },
  },
};

async function mountList(tasksData = []) {
  const { default: UserTasksList } = await import('./UserTasksList.vue');
  const pinia = createPinia();
  setActivePinia(pinia);

  const { useUserHubStore } = await import('@/stores/userHub');
  const store = useUserHubStore();
  store.tasks = tasksData;

  const refreshSpy = vi.spyOn(store, 'refreshTasks').mockResolvedValue();

  const wrapper = mount(UserTasksList, {
    global: { plugins: [pinia], ...globalConfig },
  });
  await flushPromises();

  return { wrapper, store, refreshSpy };
}

describe('UserTasksList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetModules();
  });

  it('does not auto-fetch on mount (parent page owns initial load)', async () => {
    const { refreshSpy } = await mountList();
    expect(refreshSpy).not.toHaveBeenCalled();
  });

  it('exposed refresh() calls store refreshTasks with user key', async () => {
    const { wrapper, refreshSpy } = await mountList();
    await wrapper.vm.refresh();
    expect(refreshSpy).toHaveBeenCalledWith('u1');
  });

  it('renders one q-item per task (ASGN-02)', async () => {
    const { wrapper } = await mountList([
      { _key: 't1', title: 'Task A', project_label: 'P1' },
      { _key: 't2', title: 'Task B', context_label: 'C1' },
    ]);
    expect(wrapper.findAll('.q-item-stub').length).toBe(2);
  });

  it('clicking a task navigates to taskScreen (AC-15)', async () => {
    const { wrapper } = await mountList([
      { _key: 't1', title: 'Task A', project_label: 'P1' },
    ]);
    await wrapper.find('.q-item-stub').trigger('click');
    expect(routerPushSpy).toHaveBeenCalledWith({
      name: 'taskScreen',
      params: { taskKey: 't1' },
    });
  });

  it('renders TasksEmpty when no tasks', async () => {
    const { wrapper } = await mountList([]);
    expect(wrapper.find('[data-testid="tasks-empty"]').exists()).toBe(true);
  });

  it('renders inner-loading when loading with no tasks', async () => {
    const { wrapper, store } = await mountList([]);
    store.loadingTasks = true;
    await flushPromises();
    expect(wrapper.find('[data-testid="inner-loading"]').exists()).toBe(true);
  });

  it('exposes refresh via defineExpose', async () => {
    const { wrapper } = await mountList();
    expect(wrapper.vm.refresh).toBeTypeOf('function');
  });

  it('exposes loading via defineExpose', async () => {
    const { wrapper } = await mountList();
    expect(wrapper.vm.loading).toBeDefined();
  });

  it('overdue task renders alert icon with theme-red (AC-25)', async () => {
    const { wrapper } = await mountList([
      { _key: 't1', title: 'Overdue', is_overdue: true, due_at: '2025-01-01T00:00:00Z' },
    ]);
    const icon = wrapper.find('[data-icon="mdi-alert-circle-outline"]');
    expect(icon.exists()).toBe(true);
    expect(icon.attributes('data-color')).toBe('theme-red');
  });

  it('non-overdue task renders check icon with theme-blue', async () => {
    const { wrapper } = await mountList([
      { _key: 't1', title: 'Normal', is_overdue: false, due_at: '2030-01-01T00:00:00Z' },
    ]);
    const icon = wrapper.find('[data-icon="mdi-check-circle-outline"]');
    expect(icon.exists()).toBe(true);
    expect(icon.attributes('data-color')).toBe('theme-blue');
  });
});
