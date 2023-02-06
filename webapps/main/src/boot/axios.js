import { boot } from 'quasar/wrappers'
import axios from 'axios'

import store from '@/store/index.js'

// Be careful when using SSR for cross-request state pollution
// due to creating a Singleton instance here;
// If any client changes this (global) instance, it might be a
// good idea to move this instance creation inside of the
// "export default () => {}" function below (which runs individually
// for each client)

// const api_url = process.env.NODE_ENV === 'production'
//  ? 'https://' + window.location.hostname + '/api/v1/'
//  : 'http://' + window.location.hostname + ':80'

const api_base_path = '/api'

const api = axios.create({
  // baseURL: window.location.origin + api_base_path
  baseURL: 'http://progress.localhost' + api_base_path
})

export default boot(({ app, store }) => {
  // for use inside Vue files (Options API) through this.$axios and this.$api
  api.interceptors.request.use(config => {
    config.headers.common = {
      ...config.headers.commons,
      Authorization: `Bearer ${store.getters.getToken}`
    }
    return config
  })

  app.config.globalProperties.$axios = axios
  // ^ ^ ^ this will allow you to use this.$axios (for Vue Options API form)
  //       so you won't necessarily have to import axios in each vue file

  app.config.globalProperties.$api = api
  // ^ ^ ^ this will allow you to use this.$api (for Vue Options API form)
  //       so you can easily perform requests against your app's API
})

export { axios, api }
