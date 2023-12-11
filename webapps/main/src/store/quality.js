import { api } from '@/boot/axios.js';

const quality = {
  state: {
    issue_types: [],
    issues: [],
  },

  getters: {
    getIssueData: (state) => (issue_key) => {
      return state.issues.find((i) => i._key == issue_key);
    },
    getIssueType: (state) => (issue_type_key) => {
      return state.issue_types.find((it) => it._key == issue_type_key);
    },
    getIssueCount: (state) => (open_only) => {
      return state.issues.filter((i) => (open_only == true ? i.open : true))
        .length;
    },
  },

  mutations: {
    LOAD_ISSUE_TYPES(state, types) {
      state.issue_types = types;
    },
    LOAD_ISSUES(state, issues) {
      state.issues = issues;
    },
  },

  actions: {
    getIssueTypes({ commit }, active_only = false) {
      return new Promise((resolve, reject) => {
        api
          .get('issue-type', { params: { active_only } })
          .then((resp) => {
            commit('LOAD_ISSUE_TYPES', resp.data);
            resolve();
          })
          .catch((err) => reject(err));
      });
    },
    createIssueType({ commit, dispatch }, issue_type_data) {
      return new Promise((resolve, reject) => {
        api.post('issue-type', issue_type_data).then(async (resp) => {
          const new_issue_type_key = resp.data.detail._key;
          await dispatch('getIssueTypes');
          resolve(new_issue_type_key);
        });
      });
    },
    updateIssueType({ commit, dispatch }, issue_type_data) {
      return new Promise((resolve, reject) => {
        api
          .patch(`issue-type/${issue_type_data._key}`, issue_type_data)
          .then(async () => {
            await dispatch('getIssueTypes');
            resolve();
          });
      });
    },
    getIssues({ commit }, search_params) {
      api
        .get('issue', { params: search_params })
        .then((resp) => commit('LOAD_ISSUES', resp.data));
    },
  },
};

export default quality;
