const adminRoutes = [
  {
    path: 'admin',
    name: 'adminPanel',
    component: () => import("@/views/AdminSection.vue"),
    redirect: { name: 'userLibrary' },
    meta: { scope: 'admin', screen_title: 'Impostazioni' },
    children: [
      {
        path: 'general',
        name: 'generalSettings',
        component: () => import("@/views/GeneralSettings.vue"),
        children: [
          {
            path: 'company',
            name: 'companyDetails',
            component: () => import("@/views/CompanyDetails.vue")
          },
          {
            path: 'default-phase',
            name: 'defaultPhaseParams',
            component: () => import("@/views/DefaultPhaseParams.vue")
          }
        ]
      },
      {
        path: 'users',
        name: 'userLibrary',
        component: () => import("@/views/UserLibrary.vue"),
        children: [
          {
            path: ':user_key',
            name: 'userInfo',
            component: () => import("@/components/UserInfoScreen.vue")
          },
          {
            path: 'new',
            name: 'newUser',
            component: () => import("@/views/UserNew.vue")
          },
          {
            path: ':user_key/reset-password',
            name: 'passwordReset',
            component: () => import("@/views/UserPasswordReset.vue"),
            props: true
          },
          {
            path: ':user_key/delete',
            name: 'userDelete',
            component: () => import("@/views/UserDelete.vue"),
            props: true
          }
        ]
      },
      {
        path: 'operations',
        name: 'operationLibrary',
        component: () => import("@/views/OperationLibrary.vue"),
        children: [
          {
            path: ':operation_key',
            name: 'operationDetail',
            component: () => import("@/views/OperationDetail.vue")
          },
          {
            path: 'new',
            name: 'operationNew',
            component: () => import("@/views/OperationNew.vue")
          },
          {
            path: ':operation_key/delete',
            name: 'operationDelete',
            component: () => import("@/views/OperationDelete")
          }
        ]
      }
    ]
  }
]

export default adminRoutes
