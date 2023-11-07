import { DateTime as DT } from 'luxon'

export function formatDateString(string, locale, options) {
  const date = new Date(Date.parse(string))
  return date.toLocaleDateString(locale, options) || ''
}

/**
 * @param {string} string
 * @param {string} locale
 * @param {Intl.DateTimeFormatOptions} format
 * @returns {string}
 */
export function formatDateTime(string, locale, format) {
  if (!string) {
    return '-'
  }

  return DT.fromISO(string).setLocale(locale).toLocaleString(format)
}

export function shortDateString(string, locale) {
  const options = {
    day: 'numeric',
    month: 'short',
    year: '2-digit'
  }
  if (string === undefined) {
    return '-'
  }

  return formatDateString(string, locale, options)
}

export function timestamp() {
  return DT.utc().toISO()
}
