import incoming from './incomingRoutes.js';
import inventory from './inventoryRoutes.js';
import shipment from './shipmentRoutes.js';
import transfering from './transferingRoutes.js';
import warehouse from './warehouseRoutes.js';

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
          ...warehouse,
          ...incoming,
          ...transfering,
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

  {
    path: '/configuration',
    name: 'configuration',
    component: () => import('src/views/ConfigurationPage.vue'),
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('src/views/404_NotFound.vue'),
  },
];

export default routes;
