const transferingRoutes = [
  {
    path: 'transfering',
    name: 'transferingRoot',
    component: () => import('app/src/views/warehouse/WarehouseRoot.vue'),
    meta: { scope: 'warehouse', screen_title: 'Warehouse' },
  },
];

export default transferingRoutes;
