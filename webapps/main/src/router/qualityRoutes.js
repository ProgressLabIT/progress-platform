const qualityRoutes = [
  {
    path: 'quality',
    name: 'qualityRoot',
    component: () => import("@/views/QualityRoot.vue"),
    redirect: { name: 'issueOverview' },
    meta: { scope: 'quality', screen_title: 'Quality' },
    children: [
      {
        path: 'issues',
        name: 'issueOverview',
        component: () => import("@/views/IssueOverview.vue"),
        children: [
          {
            path: 'issues/:issue_key',
            name: 'issueDetail',
            component: () => import('@/components/IssueDetail.vue'),
            props: true
          }
        ]
      },
    ]
  }
]

export default qualityRoutes
