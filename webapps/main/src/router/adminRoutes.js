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
            component: () => import("@/components/UserInfoScreen.vue"),
            props: true
          },
          {
            path: 'new',
            name: 'newUser',
            component: () => import("@/views/UserNew.vue")
          },
          {
            path: ':user_key/reset-password',
            name: 'passwordReset',
            component: () => import("@/views/UserPasswordReset.vue")
          },
          {
            path: ':user_key/delete',
            name: 'userDelete',
            component: () => import("@/views/UserDelete.vue")
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
            component: () => import("@/views/OperationDetail.vue"),
            props: true
          },
          {
            path: 'new',
            name: 'operationNew',
            component: () => import("@/views/OperationNew.vue")
          },
          {
            path: ':operation_key/delete',
            name: 'operationDelete',
            component: () => import("@/views/OperationDelete.vue")
          }
        ]
      },
      {
        path: 'issue-types',
        name: 'issueTypeLibrary',
        component: () => import("@/views/IssueTypeLibrary.vue"),
        children: [
          {
            path: ':issue_type_key',
            name: 'issueTypeDetail',
            component: () => import("@/views/IssueTypeDetail.vue"),
            props: true
          },
          {
            path: 'new',
            name: 'issueTypeNew',
            component: () => import("@/views/IssueTypeNew.vue")
          },
          {
            path: ':issue_type_key/delete',
            name: 'issueTypeDelete',
            component: () => import("@/views/IssueTypeDelete.vue"),
            props: true
          }
        ]
      },
      {
        path: 'field',
        name: 'formFieldLibrary',
        component: () => import('@/views/FormFieldLibrary.vue'),
        children: [
          {
            path: ':field_key',
            name: 'formFieldDetail',
            component: () => import("@/views/FormFieldDetail.vue") ,
            props: true
          }
        ]
      },
      {
        path: 'flows',
        name: 'flowLibrary',
        component: () => import("@/views/FlowLibrary.vue")
      }
    ]
  }
]

export default adminRoutes
