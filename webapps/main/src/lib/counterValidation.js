const YEAR_TOKENS = new Set(['%Y', '%y', '%G']);
const MONTH_TOKENS = new Set(['%m']);
const WEEK_TOKENS = new Set(['%V', '%U', '%W']);
const DOY_TOKENS = new Set(['%j']);
const DOM_TOKENS = new Set(['%d']);

function hasAny(tokens, set) {
  return tokens.some((t) => set.has(t));
}

export function validateCounterTemplate(template, frequency) {
  if (!frequency || frequency === 'none') return { valid: true };

  const tokens = (template || []).filter((t) => typeof t === 'string');
  const hasYear = hasAny(tokens, YEAR_TOKENS);
  const hasMonth = hasAny(tokens, MONTH_TOKENS);
  const hasWeek = hasAny(tokens, WEEK_TOKENS);
  const hasDoy = hasAny(tokens, DOY_TOKENS);
  const hasDom = hasAny(tokens, DOM_TOKENS);

  let ok = false;
  switch (frequency) {
    case 'year':
      ok = hasYear;
      break;
    case 'month':
      ok = hasYear && (hasMonth || hasDoy);
      break;
    case 'week':
      ok = hasYear && (hasWeek || hasDoy || (hasMonth && hasDom));
      break;
    case 'day':
      ok = hasYear && (hasDoy || (hasMonth && hasDom));
      break;
    default:
      ok = true;
  }

  return ok
    ? { valid: true }
    : { valid: false, reason: 'counter_template_token_required' };
}

const pad2 = (n) => String(n).padStart(2, '0');

function dayOfYear(d) {
  const start = Date.UTC(d.getFullYear(), 0, 0);
  const here = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate());
  return Math.floor((here - start) / 86400000);
}

function isoWeekParts(d) {
  const date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const dayNum = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - dayNum);
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((date - yearStart) / 86400000 + 1) / 7);
  return { week, year: date.getUTCFullYear() };
}

function weekMondayFirst(d) {
  const date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const dayNum = (date.getUTCDay() + 6) % 7;
  date.setUTCDate(date.getUTCDate() - dayNum);
  const yearStart = Date.UTC(d.getFullYear(), 0, 1);
  return Math.floor((date - yearStart) / 86400000 / 7);
}

function renderToken(token, tick, when) {
  switch (token) {
    case '%y':
      return String(when.getFullYear()).slice(-2);
    case '%Y':
      return String(when.getFullYear());
    case '%G':
      return String(isoWeekParts(when).year);
    case '%m':
      return pad2(when.getMonth() + 1);
    case '%d':
      return pad2(when.getDate());
    case '%j':
      return String(dayOfYear(when)).padStart(3, '0');
    case '%V':
      return pad2(isoWeekParts(when).week);
    case '%W':
      return pad2(weekMondayFirst(when));
    case '%H':
      return pad2(when.getHours());
    case '%M':
      return pad2(when.getMinutes());
  }
  const tickMatch = /^#(\d+)$/.exec(token);
  if (tickMatch) {
    return String(tick).padStart(parseInt(tickMatch[1], 10), '0');
  }
  return token;
}

export function renderCounterTemplate(template, tick = 1, when = new Date()) {
  const safeTick = Number.isFinite(Number(tick)) ? Number(tick) : 1;
  return (template || [])
    .filter((t) => typeof t === 'string')
    .map((t) => renderToken(t, safeTick, when))
    .join('');
}
