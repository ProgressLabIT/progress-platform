import { route } from 'quasar/wrappers'
import { createRouter, createMemoryHistory, createWebHistory, createWebHashHistory } from 'vue-router'
import routes from './routes'

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
    : (process.env.VUE_ROUTER_MODE === 'history' ? createWebHistory : createWebHashHistory)

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE)
  })

  function hasRoutePermission(route) {
    return store.getters.hasPermission(route.meta.scope)
  }

  Router.beforeEach((to, from, next) => {
    // Make sure user is authenticated
    const ignore_route = ['root', 'login'].includes(to.name)

    if (!ignore_route && !store.getters.isLoggedIn) {
      window.alert("Per visualizzare questa pagina è necessario fare prima l'accesso")
      next({ name: 'login', query: { redirect_to: to.fullPath } })
    }
    // Make sure user has appropriate permissions to access the page
    else {
      const not_authorized = to.matched.some( r => !hasRoutePermission(r) )
      if (not_authorized) {
        window.alert("L'utente non ha le autorizzazioni necessarie per accedere a questa pagina")
        next(false)
      }
      else {
        // Consider the navigation as an interaction > Reset session timeout
        if (!ignore_route) {
          store.commit('SET_SESSION_TIMEOUT')
        }
        next()
      }
    }
  })

  return Router
})
