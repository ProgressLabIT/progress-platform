import { api } from '@/boot/axios.js';

const job = {
  state: {
    job_list: [],
    assigned_job_list: [],
    unassigned_job_list: [],
  },

  mutations: {
    LOAD_JOBS(state, job_list) {
      state.job_list = job_list;
    },

    LOAD_ASSIGNMENTS(state, data) {
      state.assigned_job_list = data.assigned_jobs_by_operator;
      state.unassigned_job_list = data.unassigned_jobs;
    },

    UPDATE_SINGLE_JOB(state, job) {
      for (const assignment of state.assigned_job_list) {
        const idx = assignment.assigned_jobs.findIndex((j) => j._key === job._key);
        if (idx !== -1) {
          assignment.assigned_jobs.splice(idx, 1, { ...assignment.assigned_jobs[idx], ...job });
          return;
        }
      }
      const idx = state.unassigned_job_list.findIndex((j) => j._key === job._key);
      if (idx !== -1) {
        state.unassigned_job_list.splice(idx, 1, { ...state.unassigned_job_list[idx], ...job });
      }
    },

    UPDATE_ASSIGNMENT(state, { operator_key, assignment }) {
      const currentAssignment = state.assigned_job_list.find(
        ({ operator }) => operator._key === operator_key,
      );

      if (assignment.independent !== undefined) {
        currentAssignment.independent = assignment.independent;
      }
      if (assignment.jobs !== undefined) {
        currentAssignment.assigned_jobs.sort((a, b) => {
          const aIndex = assignment.jobs.indexOf(a._key);
          const bIndex = assignment.jobs.indexOf(b._key);
          return aIndex - bIndex;
        });
      }
    },
  },

  actions: {
    loadJobs({ commit }) {
      return new Promise((resolve, reject) => {
        api
          .get('job')
          .then((resp) => {
            commit('LOAD_JOBS', resp.data.detail);
            resolve();
          })
          .catch((err) => reject(err));
      });
    },

    async loadJobAssignments({ commit }, operatorKey) {
      const { data } = await api.get('job-assignment', {
        params: { user_key: operatorKey },
      });
      commit('LOAD_ASSIGNMENTS', data.detail);
    },

    updateJobs({ dispatch }, { job_updates, wo_key }) {
      return new Promise((resolve, reject) => {
        api
          .post(`job/update`, job_updates)
          .then(() => {
            dispatch('loadWorkOrderData', wo_key).then(() => resolve());
          })
          .catch((err) => reject(err));
      });
    },

    async updateJobAssignment({ commit }, { operator_key, independent, jobs }) {
      const update = {};
      if (independent !== undefined) {
        update.independent = independent;
      }
      if (jobs !== undefined) {
        update.jobs = jobs;
      }
      if (Object.keys(update).length === 0) {
        return;
      }

      await api.put(`queue/operator/${operator_key}`, {
        ...update,
      });
      commit('UPDATE_ASSIGNMENT', {
        operator_key,
        assignment: update,
      });
    },
  },
};

export default job;
