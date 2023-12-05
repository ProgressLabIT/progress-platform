import library from "./libraryRoutes.js"
import production from "./productionRoutes.js"
import operator from "./operatorRoutes.js"
import admin from "./adminRoutes.js"
import quality from "./qualityRoutes.js"
import report from "./reportRoutes.js"

const routes = [
  {
    path: "/",
    name: "root",
    component: () => import('views/MainLayout.vue'),
    redirect: { name: 'login' },
    children: [
      {
        path: "/login",
        name: 'login',
        component: () => import("views/LoginScreen.vue")
      },
      {
        path: "/app",
        children: [
          ...admin,
          ...library,
          ...production,
          ...operator,
          ...quality,
          ...report
        ]
      },
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
