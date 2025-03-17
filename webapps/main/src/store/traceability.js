import { cloneDeep } from 'lodash';
import { DateTime as DT } from 'luxon';
import { api } from '@/boot/axios';
import { sendEvent } from '@/composables/event';
import { timestamp } from '@/lib/TimeHandling';

function createEmptyBatch(state, job) {
  const job_key = job._key;
  const new_batch = {
    job_key,
    start: timestamp(),
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
  try {
    const hb_resp = await api.post(`/job/${job_key}/heartbeat`);
    if (hb_resp.response?.status === 401) {
      clearInterval(state.heartbeat);
    }
  } catch (error) {
    console.error('Error sending heartbeat:', error);
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

    LOAD_WORKING_JOB_DATA(state, { job_data, batch_data }) {
      state.working_job_data = job_data;
      state.current_batch_data = batch_data;
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
      // Remove declared component serials from job bom data if quantity has been decreased
      // for (const bom_line of state.working_job_data.wo_bom) {
      //   const component_qt = state.current_batch_data.qt_total * bom_line.qt;
      //   if (bom_line.declared_serials.length > component_qt) {
      //     bom_line.declared_serials = bom_line.declared_serials.filter(
      //       (serial) => batch_serials.includes(serial),
      //     );
      //   }
      // }
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

    async startJob({ commit, state }, { batch_serials = null }) {
      try {
        const resp = await sendEvent({
          event_type: 'JOB_STARTED',
          event_data: {
            job_key: state.working_job_data._key,
            batch_serials: batch_serials,
          },
        });

        const { new_work_session_data, batch_data, job_data } =
          resp.data.detail;

        commit('START_JOB', {
          new_work_session_data,
          batch_data,
          job_data,
          batch_serials,
        });
        commit('SET_HEARTBEAT', true);
      } catch (error) {
        console.error('Error starting job:', error);
      }
    },

    async pauseJob({ commit, state }) {
      const now = DT.utc();
      const work_session = getClosedWorkSessionData(state, now);

      try {
        await sendEvent({
          event_type: 'JOB_PAUSED',
          event_data: {
            job_key: state.working_job_data._key,
          },
        });

        commit('CLOSE_WORK_SESSION', work_session);
        commit('SET_HEARTBEAT', false);
      } catch (error) {
        console.error('Error pausing job:', error);
      }
    },

    async forcePauseJob(ctx, { job }) {
      try {
        await sendEvent({event_type: 'JOB_PAUSED', event_data: {job_key: job._key}});
      } catch (error) {
        console.error('Error force pausing job:', error);
      }
    },

    async resumeJob({ commit, state }, { batch_serials }) {
      try {
        const { data } = await sendEvent({
          event_type: 'JOB_RESUMED',
          event_data: {
            job_key: state.working_job_data._key,
            batch_serials,
          },
        });

        if (data?.detail) {
          const { job_data, batch_data } = data.detail;
          commit('UPDATE_JOB', job_data);
          if (batch_data) {
            commit('RESUME_BATCH', batch_data);
          }
        }
        commit('SET_HEARTBEAT', true);
      } catch (error) {
        console.error('Error resuming job:', error);
      }
    },

    async updateActiveBatch(
      { commit, state },
      { newBatchQuantity, batchSerials },
    ) {
      return new Promise((resolve, reject) => {
        sendEvent({
          event_type: 'ACTIVE_BATCH_CHANGED',
          event_data: {
            job_key: state.working_job_data._key,
            new_active_batch_qt: newBatchQuantity,
            batch_serials: batchSerials,
          },
        }).then((resp) => {
          const { job_data, batch_data, batch_serials } = resp.data.detail;
          commit('UPDATE_JOB', job_data);
          commit('UPDATE_BATCH', batch_data);
          commit('UPDATE_BATCH_SERIALS', batch_serials);
          resolve();
        }).catch((error) => {
          console.error('Error updating active batch:', error);
          reject(error);
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
        children: batch_components ? batch_components : [],
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

    async editStepData({ commit, state, rootGetters }, { stepKey }) {
      const batchStep = state.current_batch_data.step_data.find(
        ({ _key }) => _key === stepKey,
      );

      try {
        const formData = await getFormData(state, rootGetters, batchStep);

        const { data } = await sendEvent({
          event_type: 'STEP_EDITED',
          event_data: {
            execution_record_key: batchStep.execution_record_key,
            form_data: formData,
          },
        });
        const { job_data, batch_data } = data.detail;
        commit('UPDATE_JOB', job_data);
        commit('UPDATE_BATCH', batch_data);
        if (job_data.status === 'closed') {
          commit('SET_HEARTBEAT', false);
        }
      } catch (error) {
        console.error('Error editing step data:', error);
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
      { commit, state, rootGetters },
      { stepKey },
    ) {
      const batchStep = state.current_batch_data.step_data.find(
        ({ _key }) => _key === stepKey,
      );

      try {
        const formData = await getFormData(state, rootGetters, batchStep);

        const { data } = await sendEvent({
          event_type: 'STEP_COMPLETED',
          event_data: {
            batch_key: state.current_batch_data._key,
            step_key: batchStep._key,
            form_data: formData,
          },
        });
        const { job_data, batch_data } = data.detail;
        commit('UPDATE_JOB', job_data);
        commit('UPDATE_BATCH', batch_data);
        if (job_data.status === 'closed') {
          commit('SET_HEARTBEAT', false);
        }
      } catch (error) {
        console.error('Error completing step:', error);
      }
    },

    declareBatch({ commit, state }) {
      return new Promise((resolve, reject) => {
        const step_data = state.current_batch_data.step_data?.map(
          (batchStep) => {
            console.log(batchStep)
            return {
              execution_record_key: batchStep.execution_record_key,
              step_key: batchStep._key,
              form_data: batchStep.form_data,
            }
          },
        );
        // TODO: handle files

        sendEvent({
          event_type: 'BATCH_COMPLETED',
          event_data: {
            active_batch_key: state.current_batch_data._key,
            step_data: step_data,
            completed_batch_qt: state.current_batch_data.qt_total,
          },
        }).then((resp) => {
          let { job_data, batch_data } = resp.data.detail;

          if (!batch_data || !('step_data' in batch_data)) {
            batch_data = createEmptyBatch(state, job_data);
          }

          commit('UPDATE_JOB', job_data);
          commit('UPDATE_BATCH', batch_data);

          if (!job_data.active) {
            commit('SET_HEARTBEAT', false);
          }
          resolve();
        }).catch((error) => {
          console.error('Error declaring batch:', error);
          reject(error);
        });
      });
    },
  },
};

export default traceability;
