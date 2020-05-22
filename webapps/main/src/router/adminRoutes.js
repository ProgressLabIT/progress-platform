const adminRoutes = [
  {
    path: '/admin',
    name: 'adminPanel',
    component: () => import("@/views/AdminSection.vue"),
    redirect: { name: 'userLibrary' },
    children: [
      {
        path: 'user-list',
        name: 'userLibrary',
        component: () => import("@/views/UserLibrary.vue")
      }
    ]
  }
]

export default adminRoutes