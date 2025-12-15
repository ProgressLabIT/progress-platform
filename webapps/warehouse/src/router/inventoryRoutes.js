const inventoryRoutes = [
  {
    path: 'inventory',
    name: 'InventoryRoot',
    component: () => import('@/views/inventory/InventoryRoot.vue'),
    meta: { scope: 'warehouse', title: 'breadcrumb.inventory_root' },
    redirect: { name: 'InventoryHome' },
    children: [
      {
        path: '',
        name: 'InventoryHome',
        component: () => import('app/src/views/inventory/InventoryHome.vue'),
      },
      {
        path: 'count-session/:countSessionKey',
        name: 'InventoryCountSession',
        component: () => import('app/src/views/inventory/InventoryCountSession.vue'),
        props: true,
        meta: {
          dynamicBreadcrumb: true,
        },
      },
      {
        path: 'product',
        name: 'InventoryProduct',
        component: () => import('app/src/views/inventory/InventoryProduct.vue'),
      },
      {
        path: 'serial',
        name: 'InventorySerial',
        component: () => import('app/src/views/inventory/InventorySerial.vue'),
      },
      {
        path: 'position',
        name: 'InventoryPosition',
        component: () => import('app/src/views/inventory/InventoryPosition.vue'),
      },
    ],
  },
];

export default inventoryRoutes;
