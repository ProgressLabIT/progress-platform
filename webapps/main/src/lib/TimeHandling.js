export function formatDateString(string, locale, options) {
  let date = new Date(Date.parse(string))
  return date.toLocaleDateString(locale, options) || ''
}


export function shortDateString(string, locale) {
  let options = {
    day: '2-digit',
    month: 'short'
  }
  if (string === undefined) return '-'
  else return formatDateString(string, locale, options)
}