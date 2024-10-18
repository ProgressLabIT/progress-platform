import { date } from 'quasar';

export function calculateNextResetDate({ reset_period }) {
  function tomorrow() {
    var d = new Date();
    d.setDate(d.getDate() + 1);
    return d;
  }

  function nextweek() {
    var d = new Date();
    d.setDate(d.getDate() + ((1 + 7 - d.getDay()) % 7));
    return d;
  }

  function nextmonth() {
    var d = new Date();
    if (d.getMonth() == 11) {
      return new Date(d.getFullYear() + 1, 0, 1);
    } else {
      return new Date(d.getFullYear(), d.getMonth() + 1, 1);
    }
  }

  function nextyear() {
    var d = new Date();
    return new Date(d.getFullYear() + 1, 0, 1);
  }

  function formatResetDate(d) {
    return date.formatDate(d, 'YYYY/MM/DD');
  }

  function calculateResetDate() {
    switch (reset_period) {
      case 'day':
        return formatResetDate(tomorrow());
      case 'week':
        return formatResetDate(nextweek());
      case 'month':
        return formatResetDate(nextmonth());
      case 'year':
        return formatResetDate(nextyear());
      default:
        return null;
    }
  }

  const resetDate = calculateResetDate();

  return { resetDate };
}
