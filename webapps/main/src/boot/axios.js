import axios from 'axios';
import { boot } from 'quasar/wrappers';

// Be careful when using SSR for cross-request state pollution
// due to creating a Singleton instance here;
// If any client changes this (global) instance, it might be a
// good idea to move this instance creation inside of the
// "export default () => {}" function below (which runs individually
// for each client)

const domain =
  window.location.hostname === 'localhost'
    ? 'http://0.0.0.0:8000'
    : 'http://' + window.location.hostname;

const api_base_path = '/api';

//axios.defaults.withCredentials = true;

const api = axios.create({
  baseURL: domain + api_base_path,
});

export default boot(({ app, store }) => {
  api.interceptors.request.use((config) => {
    config.headers.common = {
      ...config.headers.commons,
      Authorization: `Bearer ${store.getters.getToken}`,
    };
    return config;
  });
  api.interceptors.response.use(
    (res) => {
      return res;
    },
    (error) => {
      if (error) {
        if (
          error.response.status === 401 &&
          error.config.url !== 'whoami' &&
          !error.config.url.includes('session')
        ) {
          //originalRequest._retry = true;
          store.dispatch('logout');
          //return app.router.push('/login');
        }
      }
      return error;
    },
  );

  app.config.globalProperties.$axios = axios;
  // ^ ^ ^ this will allow you to use this.$axios (for Vue Options API form)
  //       so you won't necessarily have to import axios in each vue file

  app.config.globalProperties.$api = api;
  // ^ ^ ^ this will allow you to use this.$api (for Vue Options API form)
  //       so you can easily perform requests against your app's API
});

export { axios, api };
