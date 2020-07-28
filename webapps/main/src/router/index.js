import Vue from "vue";
import VueRouter from "vue-router";

import library from "./libraryRoutes.js"
import production from "./productionRoutes.js"
import operator from "./operatorRoutes.js"
import admin from "./adminRoutes.js"

import store from "@/store/index"

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    name: "root",
    redirect: { name: 'login' }
  },
  {
    path: "/login",
    name: 'login',
    component: () => import("@/views/LoginScreen.vue")
  },
  
  ...admin,
  ...library,
  ...production,
  ...operator,

  {
    path: "*",
    name: "notFound",
    component: () => import ("@/views/404_NotFound.vue")
  }
] 
 

const router = new VueRouter({
  mode: "history",
  base: process.env.BASE_URL,
  routes
});



function hasRoutePermission(route) {
  return store.getters.hasPermission(route.meta.scope)
}

router.beforeEach((to, from, next) => {
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
        store.dispatch('setSessionTimeout')
      }
      
      next()
    }
  }
})

export default router;
