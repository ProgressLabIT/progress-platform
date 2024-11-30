const incomingRoutes = [
  {
    path: 'incoming',
    name: 'incomingRoot',
    component: () => import('@/views/incoming/IncomingRoot.vue'),
    meta: { scope: 'warehouse', screen_title: 'Incoming' },
    children: [
      {
        path: 'checks',
        name: 'incomingChecks',
        component: () => import('@/components/incoming/suppliers/SuppliersPage.vue')
      },
      {
        path: 'manual',
        name: 'incomingManual',
        component: () => import('@/components/incoming/products/ProductsList.vue')
      }
    ]
  },
];

export default incomingRoutes;
