const traceabilityRoutes = [
  {
    path: 'traceability',
    name: 'traceabilityRoot',
    component: () => import('@/views/traceability/TraceabilityRoot.vue'),
    redirect: { name: 'serialsOverview' },
    meta: { scope: 'traceability', screen_title: 'Traceability' },
    children: [
      {
        path: 'serials',
        name: 'serialsOverview',
        component: () =>
          import('app/src/views/traceability/SerialsOverview.vue'),
      },
    ],
  },
  {
    path: 'traceability/serials/:serialKey',
    name: 'serialDetail',
    component: () =>
          import('app/src/components/traceability/SerialDetail.vue'),
    props: true,
  },
];

export default traceabilityRoutes;
