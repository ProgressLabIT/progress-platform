const transferingRoutes = [
  {
    path: 'transfering',
    name: 'transferingRoot',
    component: () => import('@/views/WarehouseRoot.vue'),
    meta: { scope: 'warehouse', screen_title: 'Warehouse' },
  },
];

export default transferingRoutes;
