const productionRoutes = [
  {
    path: "production",
    name: "productionRoot",
    component: () => import('@/components/BaseEmptyParentRoute.vue'),
    meta: { scope: 'production', screen_title: true },
    redirect: { name: 'workOrderList' },
    children: [
      {
        path: "overview",
        name: "productionOverview",
        component: () => import("@/views/ProductionOverview.vue"),
        children: [
          {
            path: "work-order",
            name: 'workOrderList',
            component: () => import ("@/components/WorkOrderList.vue"),
          },
          {
            path: "work-order/new",
            name: "newWorkOrder",
            component: () => import("@/views/WorkOrderNew.vue")
          },
          {
            path: "job/:department?",
            name: 'jobList',
            component: () => import ("@/components/JobList.vue"),
          }
        ]
      },
      {
        path: "production/:wo_key",
        name: "workOrderScreen",
        redirect: { name: "workOrderJobs"},
        component: () => import ("@/components/WorkOrderScreen.vue"),
        props: true,
        children: [
          {
            path: "job-list",
            name: "workOrderJobs",
            component: () => import ("@/views/WorkOrderJobs.vue")
          },
          // {
          //   path: 'history',
          //   name: "workOrderHistory",
          //   component: () => import ("@/views/WorkOrderHistory.vue")
          // }
        ]
      }
    ]
  }
]

export default productionRoutes