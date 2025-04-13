import { cloneDeep } from 'lodash';
import { DateTime as DT } from 'luxon';
import { api } from '@/boot/axios';

function createEmptyBatch(state, startDT, job) {
  const job_key = job._key;
  const new_batch = {
    job_key,
    start: startDT.toISO(),
  };

  const procedure = state.working_job_data.step_sequence;
  if (procedure.length > 0) {
    new_batch.step_data = procedure.map((step) => ({
      _key: step._key,
      type: step.type,
      done: false,
      critical: false,
      form_data: [],
    }));
  }

  return new_batch;
}

async function getFormData(state, rootGetters, batchStep) {
  const formData = cloneDeep(batchStep.form_data);

  // TODO: Unify file handling logic with IssueForm
  /**
   * @type {{ type: string; form_fields: import('@/types/form').FormField[] } | undefined}
   */
  const stepDefinition = state.working_job_data.step_sequence.find(
    ({ _key }) => _key === batchStep._key,
  );
  if (stepDefinition.type === 'form') {
    const fields = stepDefinition.form_fields.map((field) => ({
      ...field,
      type: rootGetters.getCustomFieldByKey(field.custom_field_key)?.type,
      value: formData.find(
        ({ form_field_key }) => form_field_key === field._key,
      )?.value,
    }));

    const promises = fields
      .filter(({ type }) => type === 'files')
      .map(async (field) => {
        if (field.value === undefined) {
          return;
        }

        const to_delete = [];
        const to_add = [];

        field.value.forEach((file) => {
          if (file.temp) {
            to_add.push(file.content);
          } else if (file.delete) {
            to_delete.push(file.name);
          }
        });

        // update formData to only contain the file metadata
        const formDataEntry = formData.find(
          ({ form_field_key }) => form_field_key === field._key,
        );
        formDataEntry.value = field.value
          .filter((file) => !file.delete)
          .map((file) => ({
            size: file.size,
            name: file.name,
          }));

        const batch = state.current_batch_data;
        const target = {
          bucket: 'traceability',
          object_key: batch.work_order_key,
          subfolder: `${batch._key}/${batchStep._key}/${field.custom_field_key}/${field._key}`,
        };

        // Upload new files
        if (to_add.length) {
          // Populate form data
          const add_body = new FormData();
          Object.entries(target).forEach(([k, v]) => add_body.append(k, v));
          to_add.forEach((file) => add_body.append('contents', file));
          // Post files
          try {
            await api.post('/files', add_body);
          } catch (error) {
            console.error(error);
            window.alert(error);
          }
        }

        // Delete files
        if (to_delete.length) {
          try {
            await api.delete('/files', {
              data: {
                ...target,
                filenames: to_delete,
              },
            });
          } catch (error) {
            console.error(error);
            window.alert(error);
          }
        }
      });
    await Promise.all(promises);
  }

  return formData;
}

function createEvent(
  state,
  session_state,
  {
    event_type,
    timestamp,
    step_key = null,
    form_data = [],
    completed_batch_qt = null,
    step_changed_qt = null,
    batch_serials = null,
    new_active_batch_qt = null,
  },
) {
  const user_key = session_state.user._key;
  const job = state.working_job_data;
  const serials = batch_serials ? batch_serials : state.batch_serials;

  const event = {
    event_type,
    user_key,
    user_session_key: session_state.session_key,
    job_key: job._key,
    product_key: job.product_key,
    work_order_key: job.wo_key,
    phase_key: job.phase_key,
    active_batch_key: job.active_batch_key,
    project_code: job.project_code,
    step_key,
    form_data,
    completed_batch_qt,
    timestamp, // ISO format
    batch_serials: serials,
    step_changed_qt: step_changed_qt,
    new_active_batch_qt,
  };

  return event;
}

function getCurrentWorkSession(state) {
  const ws_count = state.work_session_list.length;
  return state.work_session_list[ws_count - 1];
}

function getClosedWorkSessionData(state, endDT) {
  const current_work_session = getCurrentWorkSession(state);

  const work_session = {
    ...current_work_session,
    end: endDT.toISO(),
    active: false,
  };
  return work_session;
}

async function sendHeartBeat(state) {
  const job_key = state.working_job_data._key;
  const hb_resp = await api.post(`/job/${job_key}/heartbeat`);
  if (hb_resp.response?.status === 401) {
    clearInterval(state.heartbeat);
  }
}

/** @type {import('vuex').Module} */
const traceability = {
  state: {
    working_job_data: {},
    work_session_list: [],
    current_batch_data: {},
    current_step_key: undefined,
    current_step_edit_mode: false,
    current_step_media_index: null,
    heartbeat: null,
    batch_serials: [],
    current_batch_serials: {},
    current_batch_faked_serials: {},
  },

  getters: {
    getBatchStep: (state) => (stepKey) => {
      const batchSteps = state.current_batch_data.step_data;
      if (!batchSteps) {
        return;
      }

      return batchSteps.find(({ _key }) => _key === stepKey);
    },

    getBatchSerials: (state) => () => {
      return state.batch_serials;
    },

    isCurrentStepEditMode: (state) => () => {
      return state.current_step_edit_mode;
    },
  },

  mutations: {
    START_USER_SESSION(state, data) {
      const user_data = {
        name: data.name,
        surname: data.surname,
        _key: data.user_key,
      };
      state.user = user_data;

      const session_data = { _key: data.session_key, scope: data.scope };
      state.user_session = session_data;
    },

    LOAD_WORKING_JOB_DATA(state, { job_data, batch_data, batch_serials }) {
      state.working_job_data = job_data;
      let prev_data = state.current_batch_data?.step_data;
      let prev_data_key = state.current_batch_data?._key;
      state.current_batch_data = batch_data;
      state.current_batch_serials = batch_serials;
      if (
        prev_data &&
        prev_data_key &&
        state.current_batch_data?._key === prev_data_key
      ) {
        for (const prev_obj of prev_data) {
          let prev_job_state = state.current_batch_data.step_data.find(
            (obj) => {
              return obj._key === prev_obj._key;
            },
          );
          if (prev_job_state && prev_job_state.form_data) {
            prev_job_state.form_data = prev_obj.form_data;
          }
        }
      }
    },

    START_JOB(state, { batch_data, job_data, batch_serials }) {
      // get timestamp and state metadata
      state.current_batch_data = batch_data;
      state.working_job_data = job_data;
      state.current_batch_serials = batch_serials;
    },

    CLOSE_WORK_SESSION(state, work_session) {
      // Update general list of work sessions
      const ws_list_length = state.work_session_list.length;
      state.work_session_list[ws_list_length - 1] = work_session;

      // Update Job status
      state.working_job_data.active = false;
    },

    SET_HEARTBEAT(state, alive) {
      alive
        ? (state.heartbeat = setInterval(() => sendHeartBeat(state), 10000))
        : clearInterval(state.heartbeat);
    },

    SET_CURRENT_STEP_KEY(state, stepKey) {
      state.current_step_key = stepKey;
    },

    SET_CURRENT_STEP_EDIT_MODE(state, editMode) {
      state.current_step_edit_mode = editMode;
    },

    CREATE_BATCH_STEP(state, stepKey) {
      const step = state.working_job_data.step_sequence.find(
        ({ _key }) => _key === stepKey,
      );
      // If there is no active batch, do nothing
      if (Object.keys(state.current_batch_data).length === 0) {
        return;
      }

      state.current_batch_data.step_data.push({
        _key: stepKey,
        type: step?.type,
        done: false,
        critical: false,
        form_data: [],
      });
    },

    UPDATE_STEP_FORM_DATA(state, { stepKey, index, data }) {
      const batchStep = this.getters.getBatchStep(stepKey);

      if (batchStep.form_data === undefined) {
        batchStep.form_data = [];
      }
      if (index !== undefined) {
        batchStep.form_data[index] = data;
      } else {
        batchStep.form_data.push(data);
      }
    },

    SET_STEP_EXECUTION_KEY(state, { stepKey, executionRecordKey }) {
      console.log('Test')
      const batchSteps = state.current_batch_data.step_data;
      const step = batchSteps.find(({ _key }) => _key === stepKey);
      if (step) {
        step.execution_record_key = executionRecordKey;
      }
    },

    UPDATE_JOB(state, job_data) {
      state.working_job_data = {
        /* Use spread to avoid overwriting notes,
        which are not present in the event response */
        ...state.working_job_data,
        ...job_data,
      };
    },

    UPDATE_BATCH(state, batch_data) {
      state.current_batch_data = batch_data;
    },

    RESUME_BATCH(state, batch_data) {
      let step_data = cloneDeep(state.current_batch_data?.step_data);
      state.current_batch_data = batch_data;
      state.current_batch_data.step_data = step_data;
    },

    UPDATE_BATCH_SERIALS(state, batch_serials) {
      state.current_batch_serials = batch_serials;
    },

    UPDATE_BATCH_FAKED_SERIALS(state, batch_serials) {
      state.current_batch_faked_serials = batch_serials;
    },
  },

  actions: {
    goToStep({ commit }, stepKey) {
      if (this.getters.isCurrentStepEditMode()) {
        // TODO: translation
        window.alert(
          'Salva o annulla le modifiche prima di passare a un altro step',
        );
        return;
      }
      const batchStep = this.getters.getBatchStep(stepKey);
      if (batchStep === undefined) {
        commit('CREATE_BATCH_STEP', stepKey);
      }
      commit('SET_CURRENT_STEP_KEY', stepKey);
      commit('SET_CURRENT_STEP_EDIT_MODE', false);
    },

    setStepEditMode({ commit }, editMode) {
      commit('SET_CURRENT_STEP_EDIT_MODE', editMode);
    },

    async loadWorkingJobData({ commit, dispatch }, job_key) {
      // Get job data
      const job_resp = await api.get(`job/${job_key}`);
      const job_data = job_resp.data.detail;

      // Get active batch data (if any)
      let batch_data = {};
      if (job_data.active_batch_key) {
        const batch_resp = await api.get(`batch/${job_data.active_batch_key}`);
        batch_data = batch_resp.data.detail;
      }

      const { data: batch_serials } = await api.get(
        `batch/${job_data.active_batch_key}/serials`,
      );

      commit('LOAD_WORKING_JOB_DATA', { job_data, batch_data, batch_serials });
      await dispatch('getIssues', {
        work_order_key: job_data.wo_key,
        with_links: true,
      });
    },

    async startJob({ commit, state, rootState }, { batch_serials = null }) {
      const now = DT.utc();

      // Create Event
      const event = createEvent(state, rootState.session, {
        event_type: 'JOB_STARTED',
        batch_serials: batch_serials,
        timestamp: now.toISO(),
      });

      // Post event and save new data
      api.post('event', event).then((resp) => {
        const { new_work_session_data, batch_data, job_data } =
          resp.data.detail;

        commit('START_JOB', {
          new_work_session_data,
          batch_data,
          job_data,
          batch_serials,
        });
        commit('SET_HEARTBEAT', true);
      });
    },

    async pauseJob({ commit, state, rootState }) {
      const now = DT.utc();
      const work_session = getClosedWorkSessionData(state, now);

      const event = createEvent(state, rootState.session, {
        event_type: 'JOB_PAUSED',
        timestamp: now.toISO(),
      });

      await api.post('event', event);
      commit('CLOSE_WORK_SESSION', work_session);
      commit('SET_HEARTBEAT', false);
    },

    async forcePauseJob({ state, rootState }, { job }) {
      const now = DT.utc();

      let event = createEvent(state, rootState.session, {
        event_type: 'JOB_PAUSED',
        timestamp: now.toISO(),
      });

      event = {
        ...event,
        job_key: job._key,
        product_key: job.product_key,
        work_order_key: job.wo_key,
        phase_key: job.phase_key,
        active_batch_key: job.active_batch_key,
        project_code: job.project_code,
      };

      await api.post('event', event);
    },

    async resumeJob({ commit, state, rootState }, { batch_serials }) {
      const now = DT.utc();
      // const new_work_session = createWorkSession(state, rootState.session, now)

      const event = createEvent(state, rootState.session, {
        event_type: 'JOB_RESUMED',
        timestamp: now.toISO(),
        batch_serials,
      });

      const { data } = await api.post('event', event);
      if (data?.detail) {
        const { job_data, batch_data } = data.detail;
        commit('UPDATE_JOB', job_data);
        if (batch_data) {
          commit('RESUME_BATCH', batch_data);
        }
      }
      commit('SET_HEARTBEAT', true);
    },

    async updateActiveBatch(
      { commit, state, rootState },
      { newBatchQuantity, batchSerials },
    ) {
      const now = DT.utc();
      const event = createEvent(state, rootState.session, {
        event_type: 'ACTIVE_BATCH_CHANGED',
        timestamp: now.toISO(),
        new_active_batch_qt: newBatchQuantity,
        batch_serials: batchSerials,
      });

      return new Promise((resolve) => {
        api.post('event', event).then((resp) => {
          const { job_data, batch_data, batch_serials } = resp.data.detail;
          commit('UPDATE_JOB', job_data);
          commit('UPDATE_BATCH', batch_data);
          commit('UPDATE_BATCH_SERIALS', batch_serials);
          resolve();
        });
      });
    },

    async fakeBatchSerials({ commit }, { job_key, batch_key }) {
      let key = batch_key;
      if (!key) {
        const job_resp = await api.get(`job/${job_key}`);
        const job_data = job_resp.data?.detail;
        key = job_data.active_batch_key;
      }
      let batch_serials = [];

      const { data: batch_components } = await api.get('component-batch', {
        params: {
          batch_key: key,
        },
      });

      batch_serials.push({
        _id: 'components',
        _key: 'components',
        _code: '',
        childs: batch_components ? batch_components : [],
      });

      commit('UPDATE_BATCH_FAKED_SERIALS', batch_serials);
    },

    async reloadBatchSerials({ commit }, { active_batch_key }) {
      const { data: batch_serials } = await api.get(
        `batch/${active_batch_key}/serials`,
      );

      if (batch_serials) {
        commit('UPDATE_BATCH_SERIALS', batch_serials);
      }
    },

    async editStepData({ commit, state, rootState, rootGetters }, { stepKey }) {
      const batchStep = state.current_batch_data.step_data.find(
        ({ _key }) => _key === stepKey,
      );

      const formData = await getFormData(state, rootGetters, batchStep);

      const now = DT.utc();
      const event = createEvent(state, rootState.session, {
        event_type: 'STEP_EDITED',
        step_key: batchStep._key,
        timestamp: now.toISO(),
        form_data: formData,
      });

      const { data } = await api.post('event', event);
      const { job_data, batch_data } = data.detail;
      commit('UPDATE_JOB', job_data);
      commit('UPDATE_BATCH', batch_data);
      if (job_data.status === 'closed') {
        commit('SET_HEARTBEAT', false);
      }
    },

    async reloadBatchData({ commit, state }) {
      // Get active batch data (if any)
      let batch_data = {};
      if (state.current_batch_data?._key) {
        const batch_resp = await api.get(
          `batch/${state.current_batch_data._key}`,
        );
        batch_data = batch_resp.data.detail;
      }
      commit('UPDATE_BATCH', batch_data);
    },

    async completeStep(
      { commit, state, rootState, rootGetters },
      { stepKey, batchQt },
    ) {
      const batchStep = state.current_batch_data.step_data.find(
        ({ _key }) => _key === stepKey,
      );

      const formData = await getFormData(state, rootGetters, batchStep);

      const now = DT.utc();
      const event = createEvent(state, rootState.session, {
        event_type: 'STEP_COMPLETED',
        step_key: batchStep._key,
        timestamp: now.toISO(),
        form_data: formData,
        completed_batch_qt: batchQt,
      });

      const { data } = await api.post('event', event);
      const { job_data, batch_data } = data.detail;
      commit('UPDATE_JOB', job_data);
      commit('UPDATE_BATCH', batch_data);
      if (job_data.status === 'closed') {
        commit('SET_HEARTBEAT', false);
      }
    },

    declareBatch({ commit, state, rootState }, { batch_qt, send_step_data }) {
      return new Promise((resolve) => {
        let formData = [];
        if (send_step_data && state.current_batch_data?.step_data) {
          for (const batchStep of state.current_batch_data.step_data) {
            formData = formData.concat(cloneDeep(batchStep.form_data));
          }
        }

        //TODO: handle files

        const now = DT.utc();
        /* INSERT EVENT CREATION HERE */
        const event = createEvent(state, rootState.session, {
          event_type: 'BATCH_COMPLETED',
          timestamp: now.toISO(),
          completed_batch_qt: batch_qt,
          form_data: formData,
        });

        api.post('event', event).then((resp) => {
          let { job_data, batch_data } = resp.data.detail;

          if (!batch_data || !('step_data' in batch_data)) {
            batch_data = createEmptyBatch(state, now, job_data);
          }

          commit('UPDATE_JOB', job_data);
          commit('UPDATE_BATCH', batch_data);

          if (!job_data.active) {
            commit('SET_HEARTBEAT', false);
          }
          resolve();
        });
      });
    },
  },
};

export default traceability;
