export function durationFromMillisec(millisec, {
  showDays = false,
  precision = 's',
  showPlusSign = false,
  returnValue = 'string'
} = {}) {
  const millisecondsPer = {
    second: 1000,
    minute: 1000 * 60,
    hour: 1000 * 60 * 60,
    day: 1000 * 60 * 60 * 24
  }

  const below0 = millisec < 0
  const abs = Math.abs(millisec)
  const days = +(abs / millisecondsPer.day).toFixed(0)
  const daysTrue = (days >= 1)
  const daysString = daysTrue && showDays ? days + 'g ' : ''

  const hours = showDays ? Math.floor((abs % millisecondsPer.day) / millisecondsPer.hour) : Math.floor(abs / millisecondsPer.hour)
  const hoursTrue = (hours >= 1)
  const showHours = ['h', 'm', 's', 'ms'].includes(precision)
  const hoursString = hoursTrue && showHours ? hours + 'h ' : ''

  const minutes = Math.floor((abs % millisecondsPer.hour) / millisecondsPer.minute)
  const minutesTrue = (minutes >= 1)
  const showMinutes = ['m', 's', 'ms'].includes(precision)
  const minutesString = minutesTrue && showMinutes ? minutes + 'm ' : ''

  const seconds = Math.floor((abs % millisecondsPer.minute) / millisecondsPer.second)
  const secondsTrue = (seconds >= 1)
  const showSeconds = ['s', 'ms'].includes(precision)
  const secondsString = secondsTrue && showSeconds ? seconds + 's ' : ''

  const milliseconds = abs % millisecondsPer.second
  const showMilliseconds = precision == 'ms'
  const millisecondsString = showMilliseconds ? milliseconds + 'ms' : ''

  let sign = ''
  if (!below0) sign = showPlusSign ? '+' : ''
  else sign = '-'

  const durationString = (sign + daysString + hoursString + minutesString + secondsString + millisecondsString).trim()

  const duration = {
    sign,
    d: daysTrue && showDays ? days : 0,
    h: hoursTrue ? hours : 0,
    m: minutesTrue ? minutes : 0,
    s: secondsTrue ? seconds : 0,
    ms: milliseconds,
    string: durationString
  }

  if (returnValue == 'object') {
    return duration
  } else { return duration[returnValue] }
}
