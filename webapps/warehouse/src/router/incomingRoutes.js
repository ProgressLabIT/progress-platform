const incomingRoutes = [
  {
    path: 'incoming',
    name: 'IncomingRoot',
    redirect: { name: 'IncomingManual'},
    meta: { scope: 'warehouse', screen_title: 'Incoming' },
    component: () => import ('@/views/incoming/IncomingRoot.vue'),
    children: [
      {
        path: 'checks',
        name: 'IncomingChecks',
        component: () => import ('@/components/incoming/suppliers/SuppliersPage.vue')
      },
      {
        path: 'manual',
        name: 'IncomingManual',
        redirect: { name: 'IncomingProduct' },
        children: [
          {
            path: 'product',
            name: 'IncomingProduct',
            component: () => import ('@/components/incoming/products/ProductsList.vue'),
            children: [
              {
                name: 'PrintProductLabel',
                path: 'print',
                component: () => import ('@/components/print/PrintLabelForm.vue'),
              }
            ]
          },
          {
            path: 'quantity',
            name: 'IncomingQuantity',
            component: () => import ('@/components/incoming/quantity/QuantitySelectionPage.vue'),
          },
          {
            path: 'position',
            name: 'IncomingPosition',
            component: () => import ('@/components/incoming/position/PositionsPage.vue'),
          },
          {
            path: 'routing',
            name: 'IncomingRouting',
            component: () => import ('@/components/incoming/position/ConfirmPositionsPage.vue')
          }
        ]
      }
    ]
  },
];

export default incomingRoutes;
