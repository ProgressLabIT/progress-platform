import admin from './adminRoutes.js';
import library from './libraryRoutes.js';
import operator from './operatorRoutes.js';
import production from './productionRoutes.js';
import quality from './qualityRoutes.js';
import report from './reportRoutes.js';
import task from './taskRoutes.js';
import traceability from './traceabilityRoutes.js';
import warehouse from './warehouseRoutes.js';

const routes = [
  {
    path: '/',
    name: 'root',
    component: () => import('views/MainLayout.vue'),
    redirect: { name: 'login' },
    children: [
      {
        path: '/app',
        children: [
          ...admin,
          ...library,
          ...production,
          ...operator,
          ...quality,
          ...traceability,
          ...task,
          ...warehouse,
          ...report,
          {
            path: 'user',
            name: 'userHub',
            component: () => import('views/UserHubPage.vue'),
            meta: { screen_title: true, keepAlive: true },
          },
        ],
      },
    ],
  },

  {
    path: '/login',
    name: 'login',
    component: () => import('views/LoginScreen.vue'),
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('@/views/404_NotFound.vue'),
  },
];

export default routes;
