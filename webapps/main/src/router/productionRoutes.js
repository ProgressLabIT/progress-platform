const productionRoutes = [
  {
    path: 'production',
    name: 'productionRoot',
    component: () => import('@/components/BaseEmptyParentRoute.vue'),
    meta: { scope: 'production', screen_title: true },
    redirect: { name: 'workOrderList' },
    children: [
      {
        path: 'overview',
        name: 'productionOverview',
        component: () => import('@/views/ProductionOverview.vue'),
        children: [
          {
            path: 'workorder',
            name: 'workOrderList',
            component: () => import('@/components/WorkOrderList.vue'),
            children: [
              {
                path: 'new',
                name: 'newWorkOrder',
                component: () => import('@/views/WorkOrderNew.vue'),
              },
              {
                path: ':wo_key',
                name: 'workOrderScreen',
                redirect: { name: 'workOrderJobs' },
                component: () => import('@/components/WorkOrderScreen.vue'),
                props: true,
                children: [
                  {
                    path: 'job-list',
                    name: 'workOrderJobs',
                    component: () => import('@/views/WorkOrderJobs.vue'),
                  },
                  {
                    path: 'history',
                    name: 'workOrderHistory',
                    component: () => import('@/views/WorkOrderHistory.vue'),
                  },
                  {
                    path: 'issues',
                    name: 'workOrderIssues',
                    component: () => import('@/views/IssueList.vue'),
                    props: true,
                    children: [
                      {
                        path: ':issue_key',
                        name: 'workOrderIssueDetail',
                        component: () => import('@/components/IssueDetail.vue'),
                        props: true,
                      },
                    ],
                  },
                  {
                    path: 'notes',
                    name: 'workOrderNotes',
                    component: () => import('@/views/WorkOrderNotes.vue'),
                  },
                  {
                    path: 'messages',
                    name: 'workOrderMessages',
                    component: () => import('@/components/MessageThread.vue'),
                    props: (route) => ({
                      context_key: route.params.wo_key,
                      context: 'work_order',
                    }),
                  },
                ],
              },
            ],
          },
          {
            path: 'job/:department?',
            name: 'jobList',
            component: () => import('@/components/JobList.vue'),
          },
          {
            path: 'workorder/archive',
            name: 'workOrderArchive',
            component: () => import('@/components/WorkOrderArchive.vue'),
          },
        ],
      },
    ],
  },
];

export default productionRoutes;
