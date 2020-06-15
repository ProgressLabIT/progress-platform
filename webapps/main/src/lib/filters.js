import Vue from 'vue'
import bytes from 'bytes'

import {shortDateString} from '@/lib/TimeHandling.js'
import { formatDateTime } from '@/lib/TimeHandling.js'
import { durationFromMillisec } from '@/lib/duration.js'



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

function numberFormat(value, locale) {
  return new Intl.NumberFormat(locale).format(value)
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
Vue.filter('dtFormat', formatDateTime)
Vue.filter('numberFormat', numberFormat)
