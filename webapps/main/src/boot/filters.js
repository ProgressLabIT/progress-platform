import { boot } from 'quasar/wrappers'

import bytes from 'bytes'

import { shortDateString, formatDateTime } from '@/lib/TimeHandling.js'
import { durationFromMillisec } from '@/lib/duration.js'

export function capitalize(value) {
  if (value === '') return value
  if (typeof value === "number") return value
  value = value.toString()
  return value.charAt(0).toUpperCase() + value.slice(1)
}

export function capitalizeAll(value) {
  if (typeof value === "number") return value

  // The added space makes sure no error is thrown if value is a single word only
  // It will be removed at the end by trim()
  const words = (value + ' ').split(" ")
  return "".concat(...words.map(w => capitalize(w) + ' ')).trim()
}

export function numberFormat(value, locale) {
  return new Intl.NumberFormat(locale).format(value)
}

export default boot(({ app }) => {
  app.config.globalProperties.$capitalize = capitalize
  app.config.globalProperties.$capitalizeAll = capitalizeAll
  app.config.globalProperties.$numberFormat = numberFormat
  app.config.globalProperties.$durationFromMillisec = durationFromMillisec
  app.config.globalProperties.$shortDateString = shortDateString
  app.config.globalProperties.$formatDateTime = formatDateTime

  app.config.globalProperties.$bytes = byte_size => {
    return bytes.format(byte_size, {
      decimalPlaces: 1,
      fixedDecimals: true,
      unitSeparator: ' ',
      thousandsSeparator: '.'
    })
  }
})
