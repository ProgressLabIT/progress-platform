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
        path: 'product',
        name: 'InventoryProduct',
        component: () => import('app/src/views/inventory/InventoryProduct.vue'),
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
