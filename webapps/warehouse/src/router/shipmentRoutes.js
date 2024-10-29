const shipmentRoutes = [
  {
    path: 'shipment',
    name: 'shipmentRoot',
    component: () => import('app/src/views/shipment/ShipmentRoot.vue'),
    meta: { scope: 'warehouse', screen_title: 'Shipment' },
  },
];

export default shipmentRoutes;
