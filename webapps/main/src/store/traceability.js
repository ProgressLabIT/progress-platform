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

function createEvent(
  state,
  session_state,
  {
    event_type,
    timestamp,
    step_key = null,
    form_data = [],
    completed_batch_qt = null,
  },
) {
  const user_key = session_state.user._key;
  const job = state.working_job_data;
  const batch_serials = state.batch_serials;

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
    batch_serials: batch_serials,
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

function sendHeartBeat(state) {
  const job_key = state.working_job_data._key;
  api.post(`/job/${job_key}/heartbeat`);
}

/** @type {import('vuex').Module} */
const traceability = {
  state: {
    working_job_data: {},
    work_session_list: [],
    current_batch_data: {},
    current_step_key: undefined,
    current_step_media_index: null,
    heartbeat: null,
    batch_serials: [],
  },

  getters: {
    getBatchStep: (state) => (stepKey) => {
      const batchSteps = state.current_batch_data.step_data;
      if (!batchSteps) {
        return;
      }

      return batchSteps.find(({ _key }) => _key === stepKey);
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

    LOAD_WORKING_JOB_DATA(state, { job_data, batch_data }) {
      state.working_job_data = job_data;
      state.current_batch_data = batch_data;
    },

    START_JOB(state, { batch_data, job_data }) {
      // get timestamp and state metadata
      state.current_batch_data = batch_data;
      state.working_job_data = job_data;
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
        type: step.type,
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

    UPDATE_BATCH_SERIALS(state, batch_serials) {
      state.batch_serials = batch_serials;
    },
  },

  actions: {
    goToStep({ commit }, stepKey) {
      const batchStep = this.getters.getBatchStep(stepKey);
      if (batchStep === undefined) {
        commit('CREATE_BATCH_STEP', stepKey);
      }
      commit('SET_CURRENT_STEP_KEY', stepKey);
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
      commit('LOAD_WORKING_JOB_DATA', { job_data, batch_data });
      await dispatch('getIssues', {
        work_order_key: job_data.wo_key,
        with_links: true,
      });
    },

    startJob({ commit, state, rootState }) {
      const now = DT.utc();

      // Create Event
      const event = createEvent(state, rootState.session, {
        event_type: 'JOB_STARTED',
        timestamp: now.toISO(),
      });

      // Post event and save new data
      api.post('event', event).then((resp) => {
        const { new_work_session_data, batch_data, job_data } =
          resp.data.detail;
        commit('START_JOB', { new_work_session_data, batch_data, job_data });
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

    async resumeJob({ commit, state, rootState }) {
      const now = DT.utc();
      // const new_work_session = createWorkSession(state, rootState.session, now)

      const event = createEvent(state, rootState.session, {
        event_type: 'JOB_RESUMED',
        timestamp: now.toISO(),
      });

      const { data } = await api.post('event', event);
      const { /* new_work_session_data, */ job_data } = data.detail;
      commit('UPDATE_JOB', job_data);
      commit('SET_HEARTBEAT', true);
    },

    async changeStepQuantity(
      { commit, state, rootState },
      { stepKey, batchQt },
    ) {
      const batchStep = state.current_batch_data.step_data.find(
        ({ _key }) => _key === stepKey,
      );

      const now = DT.utc();
      const event = createEvent(state, rootState.session, {
        event_type: 'STEP_QUANTITY_CHANGED',
        step_key: batchStep._key,
        timestamp: now.toISO(),
        step_changed_qt: batchQt,
      });

      const { data } = await api.post('event', event);
      const { job_data, batch_data } = data.detail;
      commit('UPDATE_JOB', job_data);
      commit('UPDATE_BATCH', batch_data);
    },

    async completeStep(
      { commit, state, rootState, rootGetters },
      { stepKey, batchQt },
    ) {
      const batchStep = state.current_batch_data.step_data.find(
        ({ _key }) => _key === stepKey,
      );

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

    declareBatch({ commit, state, rootState }, { batch_qt }) {
      return new Promise((resolve) => {
        const now = DT.utc();
        /* INSERT EVENT CREATION HERE */
        const event = createEvent(state, rootState.session, {
          event_type: 'BATCH_COMPLETED',
          timestamp: now.toISO(),
          completed_batch_qt: batch_qt,
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
