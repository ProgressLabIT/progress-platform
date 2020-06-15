import axios from 'axios'
import store from '@/store/index.js'

const api_url = 'http://' + window.location.hostname + ':8000'


const api = axios.create({  
  baseURL: api_url,
})

api.interceptors.request.use( config => {

  config.headers.common = { 
    ...config.headers.commons,
    'Authorization': `Bearer ${ store.getters.getToken }`
  }
  return config
})

export { api }