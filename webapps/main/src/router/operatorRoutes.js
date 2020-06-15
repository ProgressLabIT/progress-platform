const operatorRoutes = [
  {
    path: '/operator',
    name: 'operatorRoot',
    meta: { scope: 'operator' },
    component: () => import("@/components/BaseEmptyParentRoute.vue"),
    redirect: { name: "userJobsSelected" , query: { job: 'first' }},
    children: [
      {
        path: "select-job",
        name: "userJobs",
        component: () => import ("@/views/UserJobs.vue"),
        children: [
          {
            path: "confirm",
            name: "userJobsSelected",
            component: () => import ("@/views/UserJobsSelected.vue")
          },
          {
            path: "all",
            name: "userJobsAll",
            component: () => import ("@/views/UserJobsAll.vue")
          }
        ],
      },
      {
        path: "worksession/job/:job_key",
        name: "workSession",
        component: () => import ("@/views/WorkSessionScreen.vue"),
        props: true,
        redirect: { name: "jobSteps" },
        children: [
          {
            path: "steps",
            name: "jobSteps",
            props: true,
            component: () => import ("@/views/WorkSessionSteps.vue"),
          },
        //   {
        //     path: "docs",
        //     name: "jobDocs",
        //     component: () => import ("@/views/WorkSessionDocs.vue"),
        //   },
        //   {
        //     path: "bom",
        //     name: "jobBom",
        //     component: () => import ("@/views/WorkSessionBom.vue"),
        //   },
          // {
          //   path: "issues",
          //   name: "jobIssues",
          //   component: () => import ("@/views/WorkSessionIssues.vue")
          // }
        ]
      },
    ]
  }
]

export default operatorRoutes