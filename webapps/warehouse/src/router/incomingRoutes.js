const incomingRoutes = [
  {
    path: 'incoming',
    name: 'IncomingRoot',
    redirect: { name: 'IncomingHome'},
    meta: { scope: 'warehouse', title: 'breadcrumb.incoming_root' },
    component: () => import ('@/views/incoming/IncomingRoot.vue'),
    children: [
      {
        path: '',
        name: 'IncomingHome',
        component: () => import ('@/views/incoming/IncomingHome.vue'),
      },
      {
        path: 'list/:listKey',
        props: true,
        name: 'IncomingList',
        meta: { dynamicBreadcrumb: true },
        component: () => import ('@/views/incoming/IncomingList.vue'),
      },
      {
        path: 'manual',
        name: 'IncomingManual',
        component: () => import ('@/views/incoming/IncomingManual.vue'),
        meta: { title: 'breadcrumb.incoming_manual' }
      }
    ]
  },
];

export default incomingRoutes;
