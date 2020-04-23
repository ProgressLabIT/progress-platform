import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import vuetify from './plugins/vuetify';
import { durationFromMillisec } from '@/lib/duration.js'
import bytes from 'bytes'
import 'material-design-icons-iconfont/dist/material-design-icons.css' // Ensure you are using css-loader 
import {shortDateString} from '@/lib/TimeHandling.js'

function capitalize(value) {
  if (value === '') return value
  if (typeof value === "number") return value
  value = value.toString()
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function capitalizeAll(value) {
  if (typeof value === "number") return value

  // The added space makes sure no error is thrown if value is a single word only
  // It will be removed at the end by trim()
  let words = (value + ' ').split(" ") 
  return "".concat(...words.map( w => capitalize(w) + ' ')).trim()
}

Vue.config.productionTip = false;

Vue.prototype.$theme = {
  black: '#090C0D',
  background: '#131E21',
  surface1: '#1F2A2D',
  surface2: '#242E31',
  grey: '#707070',
  blue: '#22AED1',
  blue_bg: 'rgba(39,174,209, .3)',
  green: '#0DAB76',
  green_bg: 'rgba(13,171,118, .3)',
  red: '#E71D36',
  red_bg: 'rgba(213,29,54,.3)',
  orange: '#FF9F1C',
  orange_bg: 'rgba(255,159,28,.3)',
  white_low: 'rgba(255,255,255,.6)',
  white_high: 'rgba(255,255,255,.87)',
  white_disabled: 'rgba(255,255,255,.3)'
}

Vue.filter('capitalize', capitalize)

Vue.filter('capitalize_all', capitalizeAll)

Vue.filter('bytes', function(byte_size) {
  return bytes.format(byte_size, { 
    decimalPlaces: 1, 
    fixedDecimals: true, 
    unitSeparator: ' ',
    thousandsSeparator: '.' 
  })
})

Vue.filter('duration', durationFromMillisec)
Vue.filter('shortDateString', shortDateString)

new Vue({
  router,
  store,
  vuetify,
  render: h => h(App)
}).$mount("#app");