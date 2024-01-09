import { api } from '@/boot/axios.js';

const session = {
  state: {
    user: {
      _key: '',
      name: '',
      surname: '',
      home_page: '',
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
        home_page: data.home_page,
      };
      state.session_key = data.session_key;
      state.scope = data.scope;
      // state.session_timeout = data.timeout
    },

    CLOSE_USER_SESSION(state) {
      state.user = { name: null, surname: null, _key: null };
      state.session_key = null;
      state.scope = null;
      state.auth_token = null;

      // Make sure to cancel any residual locking mechanism after logout
      // clearTimeout(state.session_timer)
      state.session_locked = false;
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

    UPDATE_HOME_PAGE(state, newHomePage) {
      state.user.home_page = newHomePage;
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
          in the vuex store, triggering the puaseJob action, which will cause error
          because there are no active work sessions in the backend
          */
        }
      }
      await api.delete(`session/${state.session_key}`);
      commit('CLOSE_USER_SESSION');
      this.$router.push({ name: 'login' });
    },

    unlockSession({ commit }) {
      commit('TOGGLE_SESSION_LOCK', false);
      commit('SET_SESSION_TIMEOUT');
    },
  },

  getters: {
    getToken: (state) => {
      return state.auth_token;
    },

    isLoggedIn: (state) => {
      const token = state.auth_token;
      const session = state.session_key;
      const user = state.user._key;

      return token && user && session;
    },

    hasPermission: (state) => (route_scope) => {
      return RegExp(route_scope).test(state.scope);
    },

    userFullName: (state) => {
      return state.user.name + ' ' + state.user.surname;
    },

    userHomepage: (state) => {
      const userDefaultPage = state.user.home_page;
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
