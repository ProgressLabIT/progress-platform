const taskRoutes = [
  {
    path: 'task',
    name: 'taskRoot',
    component: () => import('@/views/TaskRoot.vue'),
    redirect: { name: 'taskOverview' },
    meta: { scope: 'task', screen_title: 'Task' },
    children: [
      {
        path: '',
        name: 'taskOverview',
        component: () => import('@/views/TaskOverview.vue'),
        children: [
          {
            path: ':taskKey',
            name: 'taskDetail',
            component: () => import('@/views/TaskDetail.vue'),
            props: true,
          },
        ],
      },
    ],
  },
];

export default taskRoutes;
