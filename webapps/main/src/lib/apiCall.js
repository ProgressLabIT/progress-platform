import axios from 'axios';
import store from '@/store/index.js';

// const api_url = process.env.NODE_ENV === 'production'
// 	? 'https://' + window.location.hostname + '/api/v1/'
// 	: 'http://' + window.location.hostname + ':80'

const api_base_path = '/api';

//axios.defaults.withCredentials = true;

const api = axios.create({
  baseURL: window.location.origin + api_base_path,
});

api.interceptors.request.use((config) => {
  config.headers.common = {
    ...config.headers.commons,
    Authorization: `Bearer ${store.getters.getToken}`,
  };
  return config;
});

export { api };
