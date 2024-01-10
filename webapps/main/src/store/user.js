import { isEmpty as _isEmpty } from 'lodash/fp';
import { api, axios } from '@/boot/axios.js';

const user = {
  state: {
    user_list: [],
  },

  getters: {
    operator_list: (state) => () => {
      return state.user_list.filter((u) => u.scope.includes('operator'));
    },
    user_data: (state) => (user_key) => {
      return state.user_list.filter((u) => u._key == user_key)[0];
    },
  },

  mutations: {
    LOAD_USERS(state, user_list) {
      state.user_list = user_list;
    },
  },

  actions: {
    loadUsers({ commit }, active_only = true) {
      return new Promise((resolve) => {
        api.get('user', { params: { active_only } }).then((resp) => {
          commit('LOAD_USERS', resp.data.detail);
          resolve();
        });
      });
    },

    createUser({ dispatch }, new_user_data) {
      return new Promise((resolve, reject) => {
        api
          .post('user', new_user_data)
          .then(async (resp) => {
            await dispatch('loadUsers', false);
            resolve(resp.data.detail.temp_psw);
          })
          .catch((err) => reject(err));
      });
    },

    updateUser({ dispatch }, { user_key, user_update, new_image }) {
      const api_calls = [];

      if (!_isEmpty(user_update)) {
        api_calls.push(api.patch(`user/${user_key}`, user_update));
      }

      if (new_image) {
        const body = new FormData();
        body.append('new_image', new_image);
        api_calls.push(
          api.put(`user/${user_key}/image`, body, {
            headers: {
              'Content-type': 'multipart/form-data',
            },
          }),
        );
      }

      return new Promise((resolve, reject) => {
        axios
          .all(api_calls)
          .then(async () => {
            await dispatch('loadUsers');
            resolve();
          })
          .catch((err) => reject(err));
      });
    },
  },
};

export default user;
