const incomingRoutes = [
  {
    path: 'incoming',
    name: 'incomingRoot',
    component: () => import('@/views/incoming/IncomingRoot.vue'),
    meta: { scope: 'warehouse', screen_title: 'Incoming' },
  },
];

export default incomingRoutes;
