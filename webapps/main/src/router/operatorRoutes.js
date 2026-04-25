const operatorRoutes = [
  {
    path: 'operator',
    name: 'operatorRoot',
    meta: { scope: 'operator' },
    component: () => import('@/components/BaseEmptyParentRoute.vue'),
    redirect: { name: 'userHub', query: { tab: 'jobs' } },
  },
  {
    path: 'job/:jobKey',
    name: 'workSession',
    component: () => import('@/views/WorkSessionScreen.vue'),
    props: true,
    meta: { screen_title: true, scope: 'operator' },
    children: [
      {
        path: 'steps',
        name: 'jobSteps',
        props: true,
        component: () => import('@/views/WorkSessionSteps.vue'),
      },
      {
        path: 'docs',
        name: 'jobDocs',
        component: () => import('@/views/WorkSessionDocs.vue'),
      },
      {
        path: 'bom',
        name: 'jobBom',
        component: () => import('@/views/WorkSessionBom.vue'),
      },
      {
        path: 'notes',
        name: 'jobNotes',
        component: () => import('@/views/WorkSessionNotes.vue'),
      },
      {
        path: 'issues',
        name: 'jobIssues',
        component: () => import('@/views/IssueList.vue'),
        props: true,
      },
      {
        path: 'issues/:issueKey',
        name: 'jobIssueDetail',
        component: () => import('@/components/IssueDetail.vue'),
        props: true,
      },
      {
        path: 'messages',
        name: 'jobMessages',
        component: () => import('@/components/MessageThread.vue'),
        props: () => ({ context: 'job' }),
      },
      {
        path: 'process',
        name: 'jobProcessView',
        component: () => import('@/views/WorkSessionProcess.vue'),
        props: true,
      },
    ],
  },
];

export default operatorRoutes;
