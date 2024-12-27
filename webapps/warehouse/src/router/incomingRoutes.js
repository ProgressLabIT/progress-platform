const incomingRoutes = [
  {
    path: 'incoming',
    name: 'IncomingRoot',
    redirect: { name: 'IncomingManual'},
    meta: { scope: 'warehouse', title: 'breadcrumb.incoming_root' },
    component: () => import ('@/views/incoming/IncomingRoot.vue'),
    children: [
      {
        path: 'lists',
        name: 'IncomingLists',
        component: () => import ('@/components/incoming/suppliers/SuppliersPage.vue'),
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
