import { mount } from '@vue/test-utils';
import { createStore } from 'vuex';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import WorkSessionSteps from './WorkSessionSteps.vue';

// Stub child components that import heavy dependencies
vi.mock('@/components/JobForm.vue', () => ({ default: { template: '<div data-testid="job-form"/>' } }));
vi.mock('@/components/JobInstruction.vue', () => ({ default: { template: '<div data-testid="job-instruction"/>' } }));
vi.mock('@/components/NoDataAlert.vue', () => ({ default: { template: '<div data-testid="no-data-alert"><slot/></div>' } }));

const STEP_1 = { _key: 'step_1', type: 'instruction' };
const STEP_2 = { _key: 'step_2', type: 'form' };

function makeStore(overrides = {}) {
  const currentStepKey = overrides.current_step_key ?? 'step_1';
  const batchData = overrides.batch_data ?? [
    { _key: 'step_1', done: false, critical: false },
    { _key: 'step_2', done: true, critical: false },
  ];
  const workingJobData = {
    active: true,
    product_key: 'product_1',
    phase_key: 'phase_1',
    ...(overrides.working_job_data ?? {}),
  };

  const dispatchSpy = vi.fn().mockResolvedValue(undefined);

  const store = createStore({
    getters: {},
    actions: {
      goToStep: dispatchSpy,
    },
    modules: {
      traceability: {
        namespaced: false,
        state: () => ({
          current_step_key: currentStepKey,
          current_batch_data: { step_data: batchData },
          working_job_data: workingJobData,
        }),
        mutations: {
          SET_STEP(state, key) { state.current_step_key = key; },
        },
      },
    },
  });

  // Attach spy so tests can check it
  store._dispatchSpy = dispatchSpy;
  return store;
}

function makeJob(overrides = {}) {
  return {
    step_sequence: [STEP_1, STEP_2],
    parameters: { step_check_force_order: false },
    active: true,
    product_key: 'product_1',
    phase_key: 'phase_1',
    ...overrides,
  };
}

const globalConfig = {
  stubs: {
    'q-toolbar': { template: '<div><slot/></div>' },
    'q-avatar': {
      template: '<div class="q-avatar" :style="style" @click="$emit(\'click\')"><slot/></div>',
      props: ['style'],
      emits: ['click'],
    },
  },
  config: {
    globalProperties: {
      $t: (key) => key,
      $theme: {
        green: '#4CAF50',
        green_bg: '#E8F5E9',
        grey: '#9E9E9E',
        red: '#F44336',
        red_bg: '#FFEBEE',
        blue: '#2196F3',
        text_low: '#757575',
      },
    },
  },
};

describe('WorkSessionSteps', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // VUE-08: Avatar step styling (active, done, critical)
  describe('stepStyle avatar styling (VUE-08)', () => {
    it('applies blue background to active step when job is active', () => {
      const store = makeStore({ current_step_key: 'step_1' });
      const job = makeJob();
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // stepStyle for active step_1 with job.active=true:
      // isStepActive=true, isStepDone=false, isStepCritical=false -> backgroundColor = $theme.blue
      const vm = wrapper.vm;
      const style = vm.stepStyle('step_1');
      expect(style.backgroundColor).toBe('#2196F3'); // $theme.blue
    });

    it('applies green_bg background to done but inactive step', () => {
      const store = makeStore({
        current_step_key: 'step_1',
        batch_data: [
          { _key: 'step_1', done: false, critical: false },
          { _key: 'step_2', done: true, critical: false },
        ],
      });
      const job = makeJob();
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // stepStyle for step_2: isStepActive=false (current=step_1), isStepDone=true, isStepCritical=false
      // -> backgroundColor = $theme.green_bg
      const style = wrapper.vm.stepStyle('step_2');
      expect(style.backgroundColor).toBe('#E8F5E9'); // $theme.green_bg
    });

    it('applies green background to step that is both active and done', () => {
      const store = makeStore({
        current_step_key: 'step_1',
        batch_data: [
          { _key: 'step_1', done: true, critical: false },
          { _key: 'step_2', done: false, critical: false },
        ],
      });
      const job = makeJob();
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // step_1: isStepActive=true, isStepDone=true -> backgroundColor = $theme.green
      const style = wrapper.vm.stepStyle('step_1');
      expect(style.backgroundColor).toBe('#4CAF50'); // $theme.green
    });

    it('applies red_bg to critical but inactive step', () => {
      const store = makeStore({
        current_step_key: 'step_1',
        batch_data: [
          { _key: 'step_1', done: false, critical: false },
          { _key: 'step_2', done: false, critical: true },
        ],
      });
      const job = makeJob();
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // step_2: isStepCritical=true, isStepActive=false -> backgroundColor = $theme.red_bg
      const style = wrapper.vm.stepStyle('step_2');
      expect(style.backgroundColor).toBe('#FFEBEE'); // $theme.red_bg
    });

    it('applies transparent background to step not active, not done, not critical', () => {
      const store = makeStore({
        current_step_key: 'step_1',
        batch_data: [
          { _key: 'step_1', done: false, critical: false },
          { _key: 'step_2', done: false, critical: false },
        ],
      });
      const job = makeJob();
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // step_2: not active, not done, not critical -> transparent
      const style = wrapper.vm.stepStyle('step_2');
      expect(style.backgroundColor).toBe('transparent');
    });

    it('sets cursor to pointer when step click is allowed', () => {
      const store = makeStore({ current_step_key: 'step_1' });
      const job = makeJob({ parameters: { step_check_force_order: false } });
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      const style = wrapper.vm.stepStyle('step_1');
      expect(style.cursor).toBe('pointer');
    });
  });

  // VUE-09: Step click navigation
  describe('stepClick navigation (VUE-09)', () => {
    it('dispatches goToStep when step is clicked and allowClick returns true', async () => {
      const store = makeStore({ current_step_key: 'step_1' });
      const job = makeJob({ parameters: { step_check_force_order: false } });
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // Call stepClick directly (step navigation is setter on current_step_key)
      wrapper.vm.stepClick('step_2');
      await wrapper.vm.$nextTick();

      // current_step_key setter calls this.$store.dispatch('goToStep', key)
      // Vuex action handler receives (context, payload) — check the payload
      expect(store._dispatchSpy).toHaveBeenCalledWith(
        expect.anything(),
        'step_2'
      );
    });

    it('does not navigate when force_order=true and batch_data is undefined', () => {
      const store = makeStore({
        current_step_key: 'step_1',
        batch_data: undefined,
      });
      // Override state to make batch_data undefined
      store.state.traceability.current_batch_data = undefined;

      const job = makeJob({ parameters: { step_check_force_order: true } });
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // allowClick for step index > 0 with force_order=true and batch_data=undefined returns false
      // stepClick('step_2') should not dispatch
      wrapper.vm.stepClick('step_2');
      expect(store._dispatchSpy).not.toHaveBeenCalled();
    });
  });

  // VUE-10: Component type selection (JobForm vs JobInstruction)
  describe('component type selection (VUE-10)', () => {
    it('renders JobForm when current_step.type is form', () => {
      const store = makeStore({ current_step_key: 'step_2' }); // step_2 has type='form'
      const job = makeJob();
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // current_step = step_2 (type='form') -> renders JobForm stub
      expect(wrapper.find('[data-testid="job-form"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="job-instruction"]').exists()).toBe(false);
    });

    it('renders JobInstruction when current_step.type is instruction', () => {
      const store = makeStore({ current_step_key: 'step_1' }); // step_1 has type='instruction'
      const job = makeJob();
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      // current_step = step_1 (type='instruction') -> renders JobInstruction stub
      expect(wrapper.find('[data-testid="job-instruction"]').exists()).toBe(true);
      expect(wrapper.find('[data-testid="job-form"]').exists()).toBe(false);
    });

    it('renders NoDataAlert when step_sequence is empty', () => {
      const store = makeStore({ current_step_key: undefined });
      const job = makeJob({ step_sequence: [] });
      const wrapper = mount(WorkSessionSteps, {
        props: { job },
        global: { ...globalConfig, plugins: [store] },
      });

      expect(wrapper.find('[data-testid="no-data-alert"]').exists()).toBe(true);
    });
  });
});
