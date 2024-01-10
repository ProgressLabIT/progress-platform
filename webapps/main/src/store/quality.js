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
    async getIssueTypes({ commit }, active_only = false) {
      const { data } = await api.get('issue-type', { params: { active_only } });
      commit('LOAD_ISSUE_TYPES', data);
    },
    async createIssueType({ dispatch }, issue_type_data) {
      const { data } = await api.post('issue-type', issue_type_data);
      const new_issue_type_key = data.detail._key;
      await dispatch('getIssueTypes');
      return new_issue_type_key;
    },
    async updateIssueType({ dispatch }, issue_type_data) {
      await api.patch(`issue-type/${issue_type_data._key}`, issue_type_data);
      await dispatch('getIssueTypes');
    },
    async getIssues({ commit }, search_params) {
      const { data } = await api.get('issue', { params: search_params });
      commit('LOAD_ISSUES', data);
    },
  },
};

export default quality;
