import Vue from "vue";
import VueRouter from "vue-router";
import library from "./libraryRoutes.js"
import production from "./productionRoutes.js"
import operator from "./operatorRoutes.js"
import admin from "./adminRoutes.js"



Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    redirect: { name: 'login' }
  },
  {
    path: "/login",
    name: "login",
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

export default router;
