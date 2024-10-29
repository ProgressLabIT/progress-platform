const inventoryRoutes = [
  {
    path: 'inventory',
    name: 'inventoryRoot',
    component: () => import('@/views/inventory/InventoryRoot.vue'),
    meta: { scope: 'warehouse', screen_title: 'Inventory' },
  },
];

export default inventoryRoutes;
