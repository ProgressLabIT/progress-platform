const transferRoutes = [
  {
    path: 'transfer',
    meta: { scope: 'warehouse', title: 'breadcrumb.transfer_root' },
    children: [
      {
        path: '',
        name: 'TransferRoot',
        component: () => import('app/src/views/transfering/TransferRoot.vue'),
      },
      {
        path: 'mission/:key',
        name: 'TransferMission',
        // component: () => import('app/src/views/transfering/WarehouseMissions.vue'),
        meta: { title: 'breadcrumb.transfer_missions' }
      },
      {
        path: 'manual',
        name: 'TransferManual',
        component: () => import('app/src/views/transfering/TransferManual.vue'),
        meta: { title: 'breadcrumb.transfer_manual' }
      }
    ]
  },
];

export default transferRoutes;
