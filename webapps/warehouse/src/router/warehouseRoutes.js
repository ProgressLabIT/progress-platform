const warehouseRoutes = [
  {
    path: 'warehouse',
    name: 'warehouseRoot',
    component: () => import('app/src/views/warehouse/WarehouseRoot.vue'),
    meta: { scope: 'warehouse', screen_title: 'Warehouse' },
  },
];

export default warehouseRoutes;
