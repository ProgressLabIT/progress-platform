const warehouseRoutes = [
  {
    path: 'warehouse',
    name: 'warehouseRoot',
    component: () => import('@/views/WarehouseRoot.vue'),
    meta: { scope: 'warehouse', screen_title: 'Warehouse' },
  },
];

export default warehouseRoutes;
