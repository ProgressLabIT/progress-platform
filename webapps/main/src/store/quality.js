import { api } from '@/boot/axios.js'

const quality = {

  state: {
    issue_types: []
  },

  mutations: {
    LOAD_ISSUE_TYPES(state, types) {
      state.issue_types = types
    }
  },

  actions: {
    getIssueTypes({ commit }) {
      return new Promise((resolve, reject) => {
        api.get('issue-type')
          .then( resp => {
            commit('LOAD_ISSUE_TYPES', resp.data)
            resolve()
          })
          .catch(err => reject(err))
        })
    },
    createIssueType({ commit, dispatch }, issue_type_data) {
      return new Promise((resolve, reject) => {
        api.post('issue-type', issue_type_data)
        .then( async (resp) => {
          const new_issue_type_key = resp.data.detail._key
          await dispatch('getIssueTypes')
          resolve(new_issue_type_key)
        })
      })
    },
    updateIssueType({ commit, dispatch }, issue_type_data) {
      return new Promise((resolve, reject) => {
        api.patch(`issue-type/${issue_type_data._key}`, issue_type_data)
        .then( async () => {
          await dispatch('getIssueTypes')
          resolve()
        })
      })
    }
  }
}

export default quality
