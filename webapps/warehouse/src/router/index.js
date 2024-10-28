import { Quasar } from 'quasar';
import { route } from 'quasar/wrappers';
import {
  createRouter,
  createMemoryHistory,
  createWebHistory,
  createWebHashHistory,
} from 'vue-router';
import en from '@/i18n/en.js';
import it from '@/i18n/it.js';
import routes from './routes';

/*
 * If not building with SSR mode, you can
 * directly export the Router instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Router instance.
 */

export default route(function ({ store }) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : process.env.VUE_ROUTER_MODE === 'history'
    ? createWebHistory
    : createWebHashHistory;

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
  });

  const messages = {
    en: en,
    it: it,
  };

  function getLocale() {
    const preferredLocale = store.state.session.user.preferences.locale;
    const detectedLocale = Quasar.lang.getLocale();
    const rawLocale = preferredLocale ?? detectedLocale ?? 'it';
    return rawLocale.startsWith('it') ? 'it' : 'en';
  }

  function hasRoutePermission(route) {
    return store.getters.hasPermission(route.meta.scope);
  }

  function hasValue(v) {
    return v !== undefined && v !== null;
  }

  function translate(message_code) {
    let result = messages[getLocale()];
    if (!hasValue(result)) {
      return message_code;
    }
    for (const key of message_code.split('.')) {
      result = result[key];
      if (!hasValue(result)) {
        return message_code;
      }
    }

    // Load the messages in the specified locale if available or fallback to the default one
    return hasValue(result) ? result : message_code;
  }

  Router.beforeEach(async (to, from, next) => {
    // Make sure user is authenticated
    const login_route = ['root', 'login'].includes(to.name);

    if (
      login_route &&
      (store.getters.isLoggedIn || (await store.dispatch('recognizeMe')))
    ) {
      let nextPage = to.query.redirect_to
        ? to.query.redirect_to
        : store.getters.userHomepage;
      next({ name: nextPage });
    } else if (
      !login_route &&
      !store.getters.isLoggedIn &&
      !(await store.dispatch('recognizeMe'))
    ) {
      window.alert(translate('login_page.login_first'));
      next({ name: 'login', query: { redirect_to: to.fullPath } });
    }
    // Make sure user has appropriate permissions to access the page
    else {
      const not_authorized = to.matched.some((r) => !hasRoutePermission(r));
      if (not_authorized) {
        window.alert(translate('login_page.not_authorized'));
        next(false);
      } else {
        // Consider the navigation as an interaction > Reset session timeout
        if (!login_route) {
          store.commit('SET_SESSION_TIMEOUT');
        }
        next();
      }
    }
  });

  return Router;
});
