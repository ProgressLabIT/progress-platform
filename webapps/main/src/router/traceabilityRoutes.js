const traceabilityRoutes = [
  {
    path: 'traceability',
    name: 'traceabilityRoot',
    component: () => import('@/views/TraceabilityRoot.vue'),
    redirect: { name: 'serialsOverview' },
    meta: { scope: 'traceability', screen_title: 'Traceability' },
    children: [
      {
        path: 'serials',
        name: 'serialsOverview',
        component: () => import('@/views/SerialsOverview.vue'),
        children: [
          {
            path: 'serials/:serialKey',
            name: 'serialDetail',
            component: () => import('@/components/SerialsDetail.vue'),
            props: true,
          },
        ],
      },
    ],
  },
];

export default traceabilityRoutes;
