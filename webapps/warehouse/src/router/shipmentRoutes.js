const shipmentRoutes = [
  {
    path: 'shipment',
    name: 'shipmentRoot',
    component: () => import('app/src/views/shipment/ShipmentRoot.vue'),
    meta: { scope: 'warehouse', title: 'breadcrumb.shipment_root' },
  },
];

export default shipmentRoutes;
