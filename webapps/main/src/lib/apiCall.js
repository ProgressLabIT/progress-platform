import axios from 'axios'

const api_url = 'http://' + window.location.hostname + ':8000'

export const api = axios.create({  
  baseURL: api_url
})

