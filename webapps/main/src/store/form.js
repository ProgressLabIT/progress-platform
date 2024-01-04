import { api } from '@/boot/axios.js'

/**
 * @type {import('vuex').Module}
 */
export default {
  state: {
    customFields: [],
  },

  getters: {
    customFieldsByKey: state => {
      const customFieldsByKey = {}
      state.customFields.forEach(field => {
        customFieldsByKey[field._key] = field
      })
      return customFieldsByKey
    },

    getCustomFieldByKey: (_, getters) => key => getters.customFieldsByKey[key],
  },

  mutations: {
    LOAD_CUSTOM_FIELDS(state, customFields) {
      state.customFields = customFields
    },
  },

  actions: {
    async getCustomFields({ commit }) {
      const { data } = await api.get('field')
      commit('LOAD_CUSTOM_FIELDS', data)
    }
  }
}
