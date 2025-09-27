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
      },
    ],
  },
  {
    path: 'task/:taskKey',
    name: 'taskScreen',
    meta: {
      scope: 'task',
      screen_title: 'Task',
      entity: {
        type: 'task',
        keyParam: 'taskKey'
      }
    },
    component: () => import('@/views/TaskScreen.vue'),
    props: true,
  },
];

export default taskRoutes;
