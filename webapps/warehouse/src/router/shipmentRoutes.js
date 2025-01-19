const shipmentRoutes = [
  {
    path: 'shipment',
    name: 'ShipmentRoot',
    redirect: { name: 'ShipmentHome'},
    meta: { scope: 'warehouse', title: 'breadcrumb.shipment_root' },
    component: () => import ('@/views/shipment/ShipmentRoot.vue'),
    children: [
      {
        path: '',
        name: 'ShipmentHome',
        component: () => import ('@/views/shipment/ShipmentHome.vue'),
      },
      {
        path: 'list/:listKey',
        props: true,
        name: 'ShipmentList',
        meta: { dynamicBreadcrumb: true },
        component: () => import ('app/src/views/lists/ListItems.vue'),
      },
      {
        path: 'manual',
        name: 'ShipmentManual',
        component: () => import ('@/views/shipment/ShipmentManual.vue'),
        meta: { title: 'breadcrumb.shipment_manual' }
      }
    ]
  },
];

export default shipmentRoutes;
