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
    APPEND_ISSUES(state, issues) {
      if (state.issues) {
        for (const issue of issues) {
          state.issues.push(issue);
        }
      } else {
        state.issues = issues;
      }
    },
    UPDATE_ISSUE(state, updatedIssue) {
      const issueIndex = state.issues.findIndex(issue => issue._key === updatedIssue._key);
      if (issueIndex !== -1) {
        state.issues[issueIndex] = updatedIssue;
      }
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
    async updateIssueType({ dispatch }, issueType) {
      /*
       * issue_type_data includes `print_templates`, which is not part of the
       * issue type model in the backend and the property will be ignored.
       * Templates must be updated separately.
       */

      const templateUpdates = issueType.print_templates
        .filter(({ temp, trash }) => temp || trash)
        .map(({ _key, temp }) => ({
          type: temp ? 'add' : 'remove',
          context: 'issue_type',
          context_key: issueType._key,
          template_key: _key,
        }));
      await Promise.all([
        api.patch(`issue-type/${issueType._key}`, issueType),
        api.post('update-template-assignments', templateUpdates),
      ]);
      await dispatch('getIssueTypes');
    },
    async getIssues({ commit }, search_params) {
      const { data } = await api.get('issue', { params: search_params });
      commit('LOAD_ISSUES', data);
    },
    async appendIssues({ commit }, search_params) {
      const { data } = await api.get('issue', { params: search_params });
      commit('APPEND_ISSUES', data);
    },
    async refreshIssueData({ commit }, issue_key) {
      const { data } = await api.get('issue', { params: { issue_key, with_links: true } });
      if (data && data.length > 0) {
        commit('UPDATE_ISSUE', data[0]);
      }
    },
  },
};

export default quality;
