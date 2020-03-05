import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import vuetify from './plugins/vuetify';
import { durationFromMillisec } from '@/lib/duration.js'
import bytes from 'bytes'

Vue.config.productionTip = false;

Vue.prototype.$theme = {
  black: '#090C0D',
  background: '#131E21',
  surface1: '#1F2A2D',
  surface2: '#242E31',
  grey: '#707070',
  blue: '#22AED1',
  green: '#0DAB76',
  red: '#E71D36',
  orange: '#FF9F1C',
  whitelow: 'rgba(255,255,255,.6)',
  whitehigh: 'rgba(255,255,255,.87)'
}

Vue.filter('capitalize', function(value) {
  if (!value) return ''
  value = value.toString()
  return value.charAt(0).toUpperCase() + value.slice(1)
})

Vue.filter('bytes', function(byte_size) {
  return bytes.format(byte_size, { 
    decimalPlaces: 1, 
    fixedDecimals: true, 
    unitSeparator: ' ',
    thousandsSeparator: '.' 
  })
})

Vue.filter('duration', durationFromMillisec)

new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount("#app");