const warehouseRoutes = [
  {
    path: 'warehouse',
    name: 'warehouseRoot',
    component: () => import('@/components/BaseEmptyParentRoute.vue'),
    redirect: { name: 'inventory' },
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
            path: 'inventory',
            name: 'inventory',
            component: () =>
              import('@/views/warehouse/inventory/InventoryRoot.vue'),
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
          },
          {
            path: 'lists',
            name: 'movementLists',
            component: () => import ('@/views/warehouse/lists/MovementListsRoot.vue')
          },
          {
            path: 'counting',
            name: 'counting',
            component: () =>
              import('@/views/warehouse/counting/CountingRoot.vue'),
            children: [],
          },
        ],
      },
    ],
  },
];

export default warehouseRoutes;
