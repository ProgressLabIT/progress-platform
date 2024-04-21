const adminRoutes = [
  {
    path: 'admin',
    name: 'adminPanel',
    component: () => import('@/views/AdminSection.vue'),
    redirect: { name: 'generalSettings' },
    meta: { scope: 'admin', screen_title: 'Impostazioni' },
    children: [
      {
        path: 'general',
        name: 'generalSettings',
        component: () => import('@/views/settings/GeneralSettings.vue'),
        redirect: { name: 'companyDetails' },
        children: [
          {
            path: 'company',
            name: 'companyDetails',
            component: () => import('@/views/settings/CompanyDetails.vue'),
          },
          {
            path: 'default-phase',
            name: 'defaultOperationParameters',
            component: () =>
              import('@/views/settings/DefaultOperationParams.vue'),
          },
          {
            path: 'other',
            name: 'otherSettings',
            component: () => import('@/views/settings/OtherSettings.vue'),
          },
        ],
      },
      {
        path: 'users',
        name: 'userLibrary',
        component: () => import('@/views/UserLibrary.vue'),
        children: [
          {
            path: ':user_key',
            name: 'userInfo',
            component: () => import('@/components/UserInfoScreen.vue'),
            props: true,
          },
          {
            path: 'new',
            name: 'newUser',
            component: () => import('@/views/UserNew.vue'),
          },
          {
            path: ':user_key/reset-password',
            name: 'passwordReset',
            component: () => import('@/views/UserPasswordReset.vue'),
          },
          {
            path: ':user_key/delete',
            name: 'userDelete',
            component: () => import('@/views/UserDelete.vue'),
          },
        ],
      },
      {
        path: 'operations',
        name: 'operationLibrary',
        component: () => import('@/views/OperationLibrary.vue'),
        children: [
          {
            path: ':operation_key',
            name: 'operationDetail',
            component: () => import('@/views/OperationDetail.vue'),
            props: true,
          },
          {
            path: 'new',
            name: 'operationNew',
            component: () => import('@/views/OperationNew.vue'),
          },
          {
            path: ':operation_key/delete',
            name: 'operationDelete',
            component: () => import('@/views/OperationDelete.vue'),
          },
        ],
      },
      {
        path: 'issue-types',
        name: 'issueTypeLibrary',
        component: () => import('@/views/IssueTypeLibrary.vue'),
        children: [
          {
            path: ':issueTypeKey',
            name: 'issueTypeDetail',
            component: () => import('@/views/IssueTypeDetail.vue'),
            props: true,
          },
          {
            path: 'new',
            name: 'issueTypeNew',
            component: () => import('@/views/IssueTypeNew.vue'),
          },
          {
            path: ':issueTypeKey/delete',
            name: 'issueTypeDelete',
            component: () => import('@/views/IssueTypeDelete.vue'),
            props: true,
          },
        ],
      },
      {
        path: 'serial-field',
        name: 'serialFieldLibrary',
        component: () => import('@/views/SerialFieldLibrary.vue'),
        children: [
          {
            path: ':field_key',
            name: 'serialFieldDetail',
            component: () => import('@/views/SerialFieldDetail.vue'),
            props: true,
          },
        ],
      },
      {
        path: 'field',
        name: 'formFieldLibrary',
        component: () => import('@/views/FormFieldLibrary.vue'),
        children: [
          {
            path: ':field_key',
            name: 'formFieldDetail',
            component: () => import('@/views/FormFieldDetail.vue'),
            props: true,
          },
        ],
      },
      {
        path: 'flows',
        name: 'flowLibrary',
        component: () => import('@/views/FlowLibrary.vue'),
      },
      {
        path: 'print-templates',
        name: 'printTemplateLibrary',
        component: () => import('@/views/PrintTemplateLibrary.vue'),
      },
    ],
  },
];

export default adminRoutes;
