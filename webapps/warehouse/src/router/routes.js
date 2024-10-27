const routes = [
  {
    path: '/',
    name: 'root',
    component: () => import('src/views/MainLayout.vue'),
    redirect: { name: 'login' },
    children: [
      {
        path: '/app',
        /*children: [
          ...admin,
          ...library,
          ...production,
          ...operator,
          ...quality,
          ...traceability,
          ...report,
        ],*/
      },
    ],
  },

  {
    path: '/login',
    name: 'login',
    component: () => import('src/views/LoginScreen.vue'),
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('src/views/404_NotFound.vue'),
  },
];

export default routes;
