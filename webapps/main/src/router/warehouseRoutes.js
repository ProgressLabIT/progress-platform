const warehouseRoutes = [
  {
    path: 'warehouse',
    name: 'warehouseRoot',
    component: () => import('@/components/BaseEmptyParentRoute.vue'),
    redirect: { name: 'positions' },
    meta: { scope: 'warehouse', screen_title: 'warehouse' },
    children: [
      {
        path: 'overview',
        name: 'warehouseOverview',
        component: () => import('@/views/warehouse/WarehouseRoot.vue'),
        children: [
          {
            path: 'positions',
            name: 'positions',
            component: () =>
              import('@/views/warehouse/positions/PositionsRoot.vue'),
            children: [
              {
                path: ':positionKey',
                name: 'positionDetail',
                component: () =>
                  import('@/components/warehouse/position/PositionDetail.vue'),
                props: true,
              },
              {
                path: 'new',
                name: 'positionNew',
                component: () =>
                  import('@/components/warehouse/position/PositionNewForm.vue'),
              },
            ],
          },
          {
            path: 'stock',
            name: 'stock',
            component: () => import('@/views/settings/GeneralSettings.vue'),
            children: [],
          },
          {
            path: 'missions',
            name: 'missions',
            component: () => import('@/views/settings/GeneralSettings.vue'),
            children: [],
          },
          {
            path: 'movements',
            name: 'movements',
            component: () =>
              import('@/views/warehouse/movements/MovementsRoot.vue'),
            children: [
              {
                path: 'new',
                name: 'movementNew',
                component: () =>
                  import('@/components/warehouse/movement/MovementNewForm.vue'),
              },
            ],
          },
        ],
      },
    ],
  },
];

export default warehouseRoutes;
