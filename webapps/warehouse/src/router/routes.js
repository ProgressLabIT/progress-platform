import incoming from './incomingRoutes.js';
import inventory from './inventoryRoutes.js';
import shipment from './shipmentRoutes.js';
import transfer from './transferRoutes.js';

const routes = [
  {
    path: '/',
    name: 'root',
    component: () => import('src/views/MainLayout.vue'),
    redirect: { name: 'login' },
    children: [
      {
        path: '/warehouse',
        children: [
          ...incoming,
          ...transfer,
          ...shipment,
          ...inventory,
        ],
      },
    ],
  },

  {
    path: '/login',
    name: 'login',
    component: () => import('src/views/LoginScreen.vue'),
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('src/views/404_NotFound.vue'),
  },
];

export default routes;
