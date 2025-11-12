import icons from '@quasar/extras/mdi-v6/icons.json';
import { DateTime as DT } from 'luxon';
import { debounce } from 'quasar';
import { createStore } from 'vuex';

const icon_list = icons.map((string) => {
  // Transform icon names from camelCase to kebab-case
  return [...string]
    .map((char) => {
      return char.toUpperCase() == char ? '-' + char.toLowerCase() : char;
    })
    .join('');
});

import session from './session.js';

/*
 * If not building with SSR mode, you can
 * directly export the Store instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Store instance.
 */
function resetSessionTimeoutAtStoreChange(store) {
  const mutations_to_ignore = [
    'TOGGLE_SESSION_LOCK',
    'CLOSE_SESSION',
    'SET_SESSION_TIMEOUT',
  ];
  store.subscribe(
    debounce((mutation) => {
      if (!mutations_to_ignore.includes(mutation.type)) {
        store.commit('SET_SESSION_TIMEOUT');
      }
    }, 5000)
  );
}

const store = createStore({
  state() {
    return {
      drag_options: {
        animation: 200,
        ghostClass: 'ghost',
        delay: 500,
        delayOnTouchOnly: true,
      },
      screen_title: 'warehouse',
      show_drawer: false,
      theme_colors: {},
      icons: icon_list,
    };
  },

  mutations: {
    UPDATE_SCREEN_TITLE(state, new_title) {
      state.screen_title = new_title;
    },
    SET_THEME(state, theme) {
      state.theme_colors = theme;
    },
    SHOW_DRAWER(state, value) {
      state.show_drawer = value;
    },
  },

  actions: {
    changeTheme({ commit }, theme) {
      commit('SET_THEME', theme);
    },
  },

  getters: {
    theme(state) {
      return state.theme_colors;
    },
    global_state(state) {
      return state;
    },
  },

  plugins: [resetSessionTimeoutAtStoreChange],

  modules: {
    session,
  },
});

/**
 * The following code restores the vuex state saved in localStorage
 * when closing or refreshing the tab, but locks the session, so the
 * user will have to input the password to proceed.
 *
 * If more than five minutes have elapsed since the close, the session
 * will not be restored.
 */

const persistedState = window.localStorage.getItem('TEMP_SESSION');

if (persistedState) {
  const restored_state = JSON.parse(persistedState);
  const elapsed_milliseconds =
    DT.utc().toMillis() - restored_state.last_interaction;
  const FIVE_MINUTES_MILLISECONDS = 5 * 60 * 1000;
  if (elapsed_milliseconds < FIVE_MINUTES_MILLISECONDS) {
    store.replaceState(restored_state);
    store.commit('TOGGLE_SESSION_LOCK', true);
  }
  window.localStorage.removeItem('TEMP_SESSION');
}

export default store;
