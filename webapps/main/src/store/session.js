import VueCookies from 'vue-cookies';
import { api } from '@/boot/axios.js';

const session = {
  state: {
    user: {
      _key: '',
      name: '',
      surname: '',
      preferences: {},
    },
    session_key: '',
    auth_token: '',
    scope: '',

    max_idle_minutes: 15, // minutes
    session_locked: false,
    session_timer: undefined,

    // hard_timeout: 2,
    // logout_timer: null,
  },

  mutations: {
    UPDATE_AUTH_TOKEN(state, new_token) {
      state.auth_token = new_token;
    },
    START_USER_SESSION(state, data) {
      state.user = {
        _key: data.user_key,
        name: data.name,
        surname: data.surname,
        preferences: data.preferences,
      };
      state.session_key = data.session_key;
      state.scope = data.scope;
      //state.auth_token = null;
      // state.session_timeout = data.timeout
    },

    CLOSE_USER_SESSION(state) {
      state.user = { name: null, surname: null, _key: null, preferences: {} };
      state.session_key = null;
      state.scope = null;

      // Make sure to cancel any residual locking mechanism after logout
      // clearTimeout(state.session_timer)
      state.session_locked = false;
      state.auth_token = null;
    },

    TOGGLE_SESSION_LOCK(state, locked) {
      state.session_locked = locked;
    },

    SET_SESSION_TIMEOUT(state) {
      clearTimeout(state.session_timer);

      const lockSession = () => {
        state.session_locked = true;
      };

      state.session_timer = setTimeout(
        lockSession,
        state.max_idle_minutes * 60 * 1000,
      );
    },

    UPDATE_PREFERENCES(state, preferences) {
      state.user.preferences = preferences;
    },

    UPDATE_USER_KEY(state, key) {
      state.user_key = key;
    },
  },

  actions: {
    async logout({ commit, dispatch, state, rootState }) {
      const is_working =
        rootState.traceability.working_job_data.active || false;
      if (is_working) {
        try {
          await dispatch('pauseJob');
        } catch {
          /*
          Some edge cases caused by unknown bugs may leave active work sessions
          in the Vuex store, triggering the pauseJob action, which will cause error
          because there are no active work sessions in the backend
          */
        }
      }
      try {
        await api.delete(`session/${state.session_key}`);
      } catch {
        /*force deleting session even if not present*/
      }
      await commit('CLOSE_USER_SESSION');
      await this.$router.push({ name: 'login' });
      VueCookies.delete('Authorization');
    },

    unlockSession({ commit }) {
      commit('TOGGLE_SESSION_LOCK', false);
      commit('SET_SESSION_TIMEOUT');
    },

    async updatePreferences({ commit, state }, preferencesToUpdate) {
      const updatedPreferences = {
        ...state.user.preferences,
        ...preferencesToUpdate,
      };
      await api.patch(`user/${state.user._key}`, {
        preferences: updatedPreferences,
      });
      commit('UPDATE_PREFERENCES', updatedPreferences);
    },

    async recognizeMe({ commit, state }) {
      const cookie = VueCookies.get('Authorization');
      if (cookie) {
        await commit('UPDATE_AUTH_TOKEN', cookie);
      }

      if (state.session_key) {
        return state.session_key !== 'UNRECOGNIZED';
      }

      const { data } = await api.get(`whoami`);
      let user_key = data?.detail?.user_key;
      if (user_key) {
        const { data } = await api.post(`session`, { user_key: user_key });
        if (data.detail) {
          await commit('START_USER_SESSION', data.detail);
          await commit('SET_SESSION_TIMEOUT');
        } else {
          user_key = 'UNRECOGNIZED';
          commit('UPDATE_USER_KEY', user_key);
        }
      } else {
        user_key = 'UNRECOGNIZED';
        commit('UPDATE_USER_KEY', user_key);
      }

      return user_key !== 'UNRECOGNIZED';
    },
  },

  getters: {
    getToken: (state) => {
      if (!state.auth_token) {
        return '';
      }
      return state.auth_token;
    },

    isLoggedIn: (state) => {
      const session = state.session_key;
      const user = state.user._key;

      return user && session;
    },

    hasPermission: (state) => (route_scope) => {
      return RegExp(route_scope).test(state.scope);
    },

    userFullName: (state) => {
      return state.user.name + ' ' + state.user.surname;
    },

    userHomepage: (state) => {
      const userDefaultPage = state.user.preferences.home_page;
      if (userDefaultPage) {
        return userDefaultPage;
      }

      const scopes = state.scope.split(' ');
      switch (true) {
        case scopes.includes('operator'):
          return 'operatorRoot';
        case scopes.includes('production'):
          return 'productionRoot';
        case scopes.includes('library'):
          return 'libraryRoot';
        case scopes.includes('admin'):
          return 'adminPanel';
        case scopes.includes('quality'):
          return 'qualityRoot';
        case scopes.includes('traceability'):
          return 'traceabilityRoot';
        case scopes.includes('reporting'):
          return 'reportRoot';
        default:
          throw new Error(
            'No homepage found for user with scopes: ' + scopes.join(', '),
          );
      }
    },
  },
};

export default session;
