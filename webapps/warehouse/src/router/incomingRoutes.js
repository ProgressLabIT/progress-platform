const incomingRoutes = [
  {
    path: 'incoming',
    name: 'IncomingRoot',
    redirect: { name: 'IncomingManual'},
    meta: { scope: 'warehouse', title: 'breadcrumb.incoming_root' },
    children: [
      {
        path: 'checks',
        name: 'IncomingChecks',
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
