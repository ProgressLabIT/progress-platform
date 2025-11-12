import axios from 'axios';
import { boot } from 'quasar/wrappers';
import { store } from 'src/boot/store.js';

// Default configuration
const DEFAULT_CONFIG = {
  baseURL: window.location.hostname === 'localhost'
    ? 'http://0.0.0.0:8000'
    : window.location.protocol + '//' + window.location.hostname,
  basePath: '/api'
};

// Get configuration from window.API_CONFIG or fallback to defaults
const getConfig = () => {
  if (window.API_CONFIG) {
    return {
      baseURL: window.API_CONFIG.baseURL || DEFAULT_CONFIG.baseURL,
      basePath: window.API_CONFIG.basePath || DEFAULT_CONFIG.basePath
    };
  }
  console.warn('API_CONFIG not found, using default configuration');
  return DEFAULT_CONFIG;
};

const config = getConfig();
const api = axios.create({
  baseURL: config.baseURL + config.basePath,
});

export default boot(({ app }) => {
  api.interceptors.request.use((request) => {
    const token = store?.getters?.getToken;
    if (token) {
      request.headers['Authorization'] = `Bearer ${token}`;
    }
    return request;
  });
  api.interceptors.response.use(
    (res) => {
      return res;
    },
    (error) => {
      if (error) {
        if (error?.response?.status === 401) {
          if (
            error.config.url !== 'whoami' &&
            !error.config.url.includes('session')
          ) {
            //originalRequest._retry = true;
            if (store && store.dispatch) {
              store.dispatch('logout');
            }
          }
          return error;
          //return app.router.push('/login');
        }
      }
      throw error;
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
