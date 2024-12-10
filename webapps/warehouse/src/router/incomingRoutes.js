const incomingRoutes = [
  {
    path: 'incoming',
    name: 'IncomingRoot',
    redirect: { name: 'IncomingManual'},
    meta: { scope: 'warehouse', screen_title: 'Incoming' },
    children: [
      {
        path: 'checks',
        name: 'IncomingChecks',
        component: () => import ('@/components/incoming/suppliers/SuppliersPage.vue')
      },
      {
        path: 'manual',
        name: 'IncomingManual',
        component: () => import ('@/views/incoming/IncomingManual.vue')
      }
    ]
  },
];

export default incomingRoutes;
