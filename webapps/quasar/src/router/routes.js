import library from "./libraryRoutes.js"
import production from "./productionRoutes.js"
import operator from "./operatorRoutes.js"
import admin from "./adminRoutes.js"

const routes = [
  {
    path: '/',
    component: () => import('views/MainLayout.vue'),
    children: [
      { path: '', component: () => import('pages/IndexPage.vue') }
    ]
  },
  {
    path: "/app",
    component: () => import("@/views/MainLayout.vue"),
    children: [
      ...admin,
      ...library,
      ...production,
      ...operator
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('@/views/404_NotFound.vue')
  }
]

export default routes
