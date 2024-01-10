const reportRoutes = [
  {
    path: 'report',
    name: 'reportRoot',
    meta: { scope: 'reporting', screen_title: 'Rapporti' },
    component: () => import('@/views/ReportRoot.vue'),
  },
];

export default reportRoutes;
