

const adminRoutes = [
  {
    path: '/admin',
    name: 'adminPanel',
    component: () => import("@/views/AdminSection.vue"),
    redirect: { name: 'userLibrary' },
    meta: { scope: 'admin', screen_title: 'Amministrazione di sistema' },
    children: [
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
            component: () => import ("@/views/UserNew.vue")
          },
          {
            path: ':user_key/reset-password',
            name: 'passwordReset',
            component: () => import ("@/views/UserPasswordReset.vue"),
            props: true
          },
          {
            path: ':user_key/delete',
            name: 'userDelete',
            component: () => import ("@/views/UserDelete.vue"),
            props: true
          }
        ]
      },
      
    ]
  }
]

export default adminRoutes