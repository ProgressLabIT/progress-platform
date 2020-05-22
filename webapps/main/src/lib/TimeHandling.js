import { DateTime as DT } from 'luxon'

export function formatDateString(string, locale, options) {
  let date = new Date(Date.parse(string))
  return date.toLocaleDateString(locale, options) || ''
}


export function formatDateTime(string, locale, format) {
  if (string === undefined) return '-'
  else return DT.fromISO(string).setLocale(locale).toFormat(format)
}

export function shortDateString(string, locale) {
  let options = {
    day: '2-digit',
    month: 'short'
  }
  if (string === undefined) return '-'
  else return formatDateString(string, locale, options)
}