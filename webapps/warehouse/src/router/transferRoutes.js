const transferRoutes = [
  {
    path: 'transfer',
    name: 'TransferRoot',
    meta: { scope: 'warehouse', title: 'breadcrumb.transfer_root' },
    redirect: { name: 'TransferManualRoot' },
    children: [
      {
        path: 'mission',
        name: 'TransferMissions',
        // component: () => import('app/src/views/transfering/WarehouseMissions.vue'),
        meta: { title: 'breadcrumb.transfer_missions' }
      },
      {
        path: 'manual',
        name: 'TransferManualRoot',
        component: () => import('app/src/views/transfering/TransferManualRoot.vue'),
        meta: { title: 'breadcrumb.transfer_manual' }
      }
    ]
  },
];

export default transferRoutes;
