import { describe, it, expect } from 'vitest';
import { evaluateComputed, extractTokens, buildValuesMap } from './computedResolver.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function vals(obj) {
  return new Map(Object.entries(obj));
}

// ---------------------------------------------------------------------------
// Arithmetic
// ---------------------------------------------------------------------------

describe('arithmetic', () => {
  it('adds two numbers', () => {
    expect(evaluateComputed('2 + 3', vals({}))).toBe(5);
  });

  it('respects operator precedence (* before +)', () => {
    expect(evaluateComputed('2 + 3 * 4', vals({}))).toBe(14);
  });

  it('handles parentheses', () => {
    expect(evaluateComputed('(2 + 3) * 4', vals({}))).toBe(20);
  });

  it('handles subtraction and division', () => {
    expect(evaluateComputed('10 - 3', vals({}))).toBe(7);
    expect(evaluateComputed('10 / 4', vals({}))).toBe(2.5);
  });

  it('handles unary minus', () => {
    expect(evaluateComputed('-5 + 3', vals({}))).toBe(-2);
  });

  it('division by zero returns 0', () => {
    expect(evaluateComputed('10 / 0', vals({}))).toBe(0);
  });

  it('handles decimal numbers', () => {
    expect(evaluateComputed('1.5 * 2', vals({}))).toBe(3);
  });

  it('resolves token values for arithmetic', () => {
    const v = vals({ 'field::Qty': '10', 'field::Price': '25.5' });
    expect(evaluateComputed('{{field::Qty}} * {{field::Price}}', v)).toBe(255);
  });

  it('treats missing tokens as empty string / 0 in arithmetic', () => {
    expect(evaluateComputed('{{field::Missing}} * 5', vals({}))).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// String concatenation (+ auto-coercion)
// ---------------------------------------------------------------------------

describe('string concatenation', () => {
  it('concatenates when one side is a string literal', () => {
    expect(evaluateComputed('"hello" + " world"', vals({}))).toBe('hello world');
  });

  it('concatenates token values that are non-numeric', () => {
    const v = vals({ 'field::Code': 'ABC', 'field::Num': '123' });
    expect(evaluateComputed('{{field::Code}} + "-" + {{field::Num}}', v)).toBe('ABC-123');
  });

  it('adds when both token values are numeric strings', () => {
    const v = vals({ 'field::A': '10', 'field::B': '20' });
    expect(evaluateComputed('{{field::A}} + {{field::B}}', v)).toBe(30);
  });
});

// ---------------------------------------------------------------------------
// Built-in functions: String
// ---------------------------------------------------------------------------

describe('CONCAT', () => {
  it('joins arguments', () => {
    const v = vals({ 'product.code': 'WIDGET', 'field::Batch': '42' });
    expect(evaluateComputed('CONCAT({{product.code}}, "-", {{field::Batch}})', v)).toBe('WIDGET-42');
  });

  it('handles single argument', () => {
    expect(evaluateComputed('CONCAT("hello")', vals({}))).toBe('hello');
  });
});

describe('UPPER / LOWER', () => {
  it('uppercases a string', () => {
    expect(evaluateComputed('UPPER("hello")', vals({}))).toBe('HELLO');
  });

  it('lowercases a string', () => {
    expect(evaluateComputed('LOWER("HELLO")', vals({}))).toBe('hello');
  });
});

// ---------------------------------------------------------------------------
// Built-in functions: Math
// ---------------------------------------------------------------------------

describe('ROUND', () => {
  it('rounds to nearest integer by default', () => {
    expect(evaluateComputed('ROUND(3.7)', vals({}))).toBe(4);
  });

  it('rounds to specified decimals', () => {
    expect(evaluateComputed('ROUND(3.14159, 2)', vals({}))).toBe(3.14);
  });

  it('works with token values', () => {
    const v = vals({ 'field::Total': '99.999' });
    expect(evaluateComputed('ROUND({{field::Total}}, 1)', v)).toBe(100);
  });
});

describe('ABS / CEIL / FLOOR', () => {
  it('computes absolute value', () => {
    expect(evaluateComputed('ABS(-7)', vals({}))).toBe(7);
  });

  it('computes ceiling', () => {
    expect(evaluateComputed('CEIL(3.1)', vals({}))).toBe(4);
  });

  it('computes floor', () => {
    expect(evaluateComputed('FLOOR(3.9)', vals({}))).toBe(3);
  });
});

// ---------------------------------------------------------------------------
// Built-in functions: Date
// ---------------------------------------------------------------------------

describe('FORMAT_DATE', () => {
  it('formats an ISO date string', () => {
    expect(evaluateComputed('FORMAT_DATE("2024-06-15T10:30:00Z", "DD/MM/YYYY")', vals({}))).toBe('15/06/2024');
  });

  it('formats with time components', () => {
    const result = evaluateComputed('FORMAT_DATE("2024-06-15T10:05:03Z", "YYYY-MM-DD HH:mm:ss")', vals({}));
    expect(result).toMatch(/^2024-06-15 \d{2}:\d{2}:\d{2}$/);
  });

  it('returns empty for invalid date', () => {
    expect(evaluateComputed('FORMAT_DATE("not-a-date", "DD/MM/YYYY")', vals({}))).toBe('');
  });

  it('formats ISO week number with IW token', () => {
    // 2024-06-15 is a Saturday in ISO week 24
    expect(evaluateComputed('FORMAT_DATE("2024-06-15T10:30:00Z", "IW")', vals({}))).toBe('24');
  });

  it('formats ISO week-year with IYYY token', () => {
    expect(evaluateComputed('FORMAT_DATE("2024-06-15T10:30:00Z", "IW/IYYY")', vals({}))).toBe('24/2024');
  });

  it('formats ISO week-year short with IYY token', () => {
    expect(evaluateComputed('FORMAT_DATE("2024-06-15T10:30:00Z", "IW/IYY")', vals({}))).toBe('24/24');
  });

  it('handles year boundary where ISO week-year differs from calendar year', () => {
    // 2024-12-30 is a Monday → ISO week 1 of 2025
    expect(evaluateComputed('FORMAT_DATE("2024-12-30T12:00:00Z", "IW/IYYY")', vals({}))).toBe('01/2025');
    // Calendar year is still 2024
    expect(evaluateComputed('FORMAT_DATE("2024-12-30T12:00:00Z", "DD/MM/YYYY")', vals({}))).toBe('30/12/2024');
  });

  it('pads single-digit ISO week with leading zero', () => {
    // 2025-01-06 is Monday of ISO week 2
    expect(evaluateComputed('FORMAT_DATE("2025-01-06T12:00:00Z", "IW")', vals({}))).toBe('02');
  });
});

describe('DAYS_BETWEEN', () => {
  it('computes days between two dates', () => {
    expect(evaluateComputed('DAYS_BETWEEN("2024-01-01", "2024-01-31")', vals({}))).toBe(30);
  });

  it('returns absolute value regardless of order', () => {
    expect(evaluateComputed('DAYS_BETWEEN("2024-01-31", "2024-01-01")', vals({}))).toBe(30);
  });

  it('returns 0 for same date', () => {
    expect(evaluateComputed('DAYS_BETWEEN("2024-06-15", "2024-06-15")', vals({}))).toBe(0);
  });

  it('returns 0 for invalid dates', () => {
    expect(evaluateComputed('DAYS_BETWEEN("bad", "worse")', vals({}))).toBe(0);
  });
});

describe('DATE_ADD', () => {
  it('adds years', () => {
    const result = evaluateComputed('DATE_ADD("2024-01-15T12:00:00Z", 2, "years")', vals({}));
    expect(result).toContain('2026-01-15');
  });

  it('adds months', () => {
    const result = evaluateComputed('DATE_ADD("2024-01-15T12:00:00Z", 3, "months")', vals({}));
    expect(result).toContain('2024-04-15');
  });

  it('adds days', () => {
    const result = evaluateComputed('DATE_ADD("2024-01-15T12:00:00Z", 10, "days")', vals({}));
    expect(result).toContain('2024-01-25');
  });

  it('subtracts with negative amount', () => {
    const result = evaluateComputed('DATE_ADD("2024-06-15T12:00:00Z", -30, "days")', vals({}));
    expect(result).toContain('2024-05-16');
  });

  it('returns empty for invalid date', () => {
    expect(evaluateComputed('DATE_ADD("invalid", 1, "days")', vals({}))).toBe('');
  });
});

describe('YEAR / MONTH / DAY', () => {
  it('extracts year', () => {
    expect(evaluateComputed('YEAR("2024-06-15")', vals({}))).toBe(2024);
  });

  it('extracts month (1-indexed)', () => {
    expect(evaluateComputed('MONTH("2024-06-15")', vals({}))).toBe(6);
  });

  it('extracts day', () => {
    expect(evaluateComputed('DAY("2024-06-15")', vals({}))).toBe(15);
  });

  it('returns 0 for invalid date', () => {
    expect(evaluateComputed('YEAR("nope")', vals({}))).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// WEEK
// ---------------------------------------------------------------------------

describe('WEEK', () => {
  it('returns ISO week number', () => {
    // 2024-01-01 is a Monday → ISO week 1
    expect(evaluateComputed('WEEK("2024-01-01")', vals({}))).toBe(1);
  });

  it('returns correct week mid-year', () => {
    // 2024-06-15 is a Saturday → ISO week 24
    expect(evaluateComputed('WEEK("2024-06-15")', vals({}))).toBe(24);
  });

  it('returns 0 for invalid date', () => {
    expect(evaluateComputed('WEEK("nope")', vals({}))).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Comparison operators
// ---------------------------------------------------------------------------

describe('comparisons', () => {
  it('== compares equal strings', () => {
    const v = vals({ 'field::A': 'hello' });
    expect(evaluateComputed('{{field::A}} == "hello"', v)).toBe(true);
  });

  it('== compares unequal strings', () => {
    const v = vals({ 'field::A': 'hello' });
    expect(evaluateComputed('{{field::A}} == "world"', v)).toBe(false);
  });

  it('!= works', () => {
    const v = vals({ 'field::A': 'hello' });
    expect(evaluateComputed('{{field::A}} != "world"', v)).toBe(true);
  });

  it('< > <= >= work on numbers', () => {
    expect(evaluateComputed('3 < 5', vals({}))).toBe(true);
    expect(evaluateComputed('5 > 3', vals({}))).toBe(true);
    expect(evaluateComputed('3 <= 3', vals({}))).toBe(true);
    expect(evaluateComputed('3 >= 4', vals({}))).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// IF function
// ---------------------------------------------------------------------------

describe('IF', () => {
  it('returns then-value when condition is true', () => {
    expect(evaluateComputed('IF(1 == 1, "yes", "no")', vals({}))).toBe('yes');
  });

  it('returns else-value when condition is false', () => {
    expect(evaluateComputed('IF(1 == 2, "yes", "no")', vals({}))).toBe('no');
  });

  it('treats non-empty string as truthy', () => {
    const v = vals({ 'field::X': 'A' });
    expect(evaluateComputed('IF({{field::X}}, 12, 6)', v)).toBe(12);
  });

  it('treats empty string as falsy', () => {
    const v = vals({ 'field::X': '' });
    expect(evaluateComputed('IF({{field::X}}, 12, 6)', v)).toBe(6);
  });

  it('works with comparison as condition', () => {
    const v = vals({ 'serial.extra.class': 'A' });
    expect(evaluateComputed('IF({{serial.extra.class}} == "A", 12, 6)', v)).toBe(12);
    expect(evaluateComputed('IF({{serial.extra.class}} == "B", 12, 6)', v)).toBe(6);
  });

  it('composes with DATE_ADD for the real-world use case', () => {
    const v = vals({ 'serial.extra.class': 'A', 'serial.extra.production_date': '2024-03-15T12:00:00Z' });
    const expr = 'CONCAT(WEEK(DATE_ADD({{serial.extra.production_date}}, IF({{serial.extra.class}} == "A", 12, 6), "months")), "/", YEAR(DATE_ADD({{serial.extra.production_date}}, IF({{serial.extra.class}} == "A", 12, 6), "months")))';
    const result = evaluateComputed(expr, v);
    // 2024-03-15 + 12 months = 2025-03-15 → ISO week 11, year 2025
    expect(result).toBe('11/2025');
  });
});

// ---------------------------------------------------------------------------
// SPLIT
// ---------------------------------------------------------------------------

describe('SPLIT', () => {
  it('splits by delimiter and returns indexed part', () => {
    expect(evaluateComputed('SPLIT("12/2026", "/", 0)', vals({}))).toBe('12');
    expect(evaluateComputed('SPLIT("12/2026", "/", 1)', vals({}))).toBe('2026');
  });

  it('returns empty for out-of-range index', () => {
    expect(evaluateComputed('SPLIT("a-b", "-", 5)', vals({}))).toBe('');
  });

  it('works with token values', () => {
    const v = vals({ 'field::Input': '38/2025' });
    expect(evaluateComputed('SPLIT({{field::Input}}, "/", 0)', v)).toBe('38');
    expect(evaluateComputed('SPLIT({{field::Input}}, "/", 1)', v)).toBe('2025');
  });

  it('splits by multi-char delimiter', () => {
    expect(evaluateComputed('SPLIT("a::b::c", "::", 2)', vals({}))).toBe('c');
  });
});

// ---------------------------------------------------------------------------
// NOW
// ---------------------------------------------------------------------------

describe('NOW', () => {
  it('returns an ISO date string', () => {
    const result = evaluateComputed('NOW()', vals({}));
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it('is usable inside other functions', () => {
    const result = evaluateComputed('YEAR(NOW())', vals({}));
    expect(result).toBe(new Date().getFullYear());
  });
});

// ---------------------------------------------------------------------------
// DATE (date builder)
// ---------------------------------------------------------------------------

describe('DATE', () => {
  it('builds from year only (Y) → Jan 1', () => {
    const result = evaluateComputed('DATE("Y", 2026)', vals({}));
    expect(result).toContain('2026-01-01');
  });

  it('builds from year + month (YM) → 1st of that month', () => {
    const result = evaluateComputed('DATE("YM", 2026, 6)', vals({}));
    expect(result).toContain('2026-06-01');
  });

  it('builds from year + month + day (YMD)', () => {
    const result = evaluateComputed('DATE("YMD", 2026, 3, 15)', vals({}));
    expect(result).toContain('2026-03-15');
  });

  it('builds from year + ISO week (YW) → Monday of that week', () => {
    // ISO week 1 of 2024: Mon 2024-01-01
    const result = evaluateComputed('DATE("YW", 2024, 1)', vals({}));
    expect(result).toContain('2024-01-01');
  });

  it('YW handles mid-year weeks', () => {
    // Week 24 of 2024 starts Mon 2024-06-10
    const result = evaluateComputed('DATE("YW", 2024, 24)', vals({}));
    expect(result).toContain('2024-06-10');
  });

  it('round-trips with WEEK/YEAR', () => {
    // Build date from week 12, 2026 → extract week/year back
    const week = evaluateComputed('WEEK(DATE("YW", 2026, 12))', vals({}));
    const year = evaluateComputed('YEAR(DATE("YW", 2026, 12))', vals({}));
    expect(week).toBe(12);
    expect(year).toBe(2026);
  });

  it('returns empty for unknown format', () => {
    expect(evaluateComputed('DATE("XYZ", 2026)', vals({}))).toBe('');
  });
});

// ---------------------------------------------------------------------------
// Real-world: week/year input + conditional month offset
// ---------------------------------------------------------------------------

describe('week/year expiry use case', () => {
  it('splits week/year input, adds 6 months, formats back', () => {
    const v = vals({ 'field::Input': '12/2026', 'serial.extra.class': 'B' });
    const expr = [
      'CONCAT(',
      '  WEEK(DATE_ADD(DATE("YW", SPLIT({{field::Input}}, "/", 1), SPLIT({{field::Input}}, "/", 0)), IF({{serial.extra.class}} == "A", 12, 6), "months")),',
      '  "/",',
      '  YEAR(DATE_ADD(DATE("YW", SPLIT({{field::Input}}, "/", 1), SPLIT({{field::Input}}, "/", 0)), IF({{serial.extra.class}} == "A", 12, 6), "months"))',
      ')',
    ].join('');
    const result = evaluateComputed(expr, v);
    // Week 12 of 2026 → Mon 2026-03-16, + 6 months → 2026-09-16 → week 38
    expect(result).toBe('38/2026');
  });

  it('splits week/year input, adds 12 months, formats back', () => {
    const v = vals({ 'field::Input': '12/2026', 'serial.extra.class': 'A' });
    const expr = [
      'CONCAT(',
      '  WEEK(DATE_ADD(DATE("YW", SPLIT({{field::Input}}, "/", 1), SPLIT({{field::Input}}, "/", 0)), IF({{serial.extra.class}} == "A", 12, 6), "months")),',
      '  "/",',
      '  YEAR(DATE_ADD(DATE("YW", SPLIT({{field::Input}}, "/", 1), SPLIT({{field::Input}}, "/", 0)), IF({{serial.extra.class}} == "A", 12, 6), "months"))',
      ')',
    ].join('');
    const result = evaluateComputed(expr, v);
    // Week 12 of 2026 → Mon 2026-03-16, + 12 months → 2027-03-16 → week 11
    expect(result).toBe('11/2027');
  });

  it('simplified with FORMAT_DATE IW/IYYY — 6 month offset', () => {
    const v = vals({ 'field::Input': '12/2026', 'serial.extra.class': 'B' });
    const expr = 'FORMAT_DATE(DATE_ADD(DATE("YW", SPLIT({{field::Input}}, "/", 1), SPLIT({{field::Input}}, "/", 0)), IF({{serial.extra.class}} == "A", 12, 6), "months"), "IW/IYYY")';
    const result = evaluateComputed(expr, v);
    expect(result).toBe('38/2026');
  });

  it('simplified with FORMAT_DATE IW/IYYY — 12 month offset', () => {
    const v = vals({ 'field::Input': '12/2026', 'serial.extra.class': 'A' });
    const expr = 'FORMAT_DATE(DATE_ADD(DATE("YW", SPLIT({{field::Input}}, "/", 1), SPLIT({{field::Input}}, "/", 0)), IF({{serial.extra.class}} == "A", 12, 6), "months"), "IW/IYYY")';
    const result = evaluateComputed(expr, v);
    expect(result).toBe('11/2027');
  });
});

// ---------------------------------------------------------------------------
// Composable expressions (nested function calls)
// ---------------------------------------------------------------------------

describe('composable expressions', () => {
  it('FORMAT_DATE wrapping DATE_ADD', () => {
    const result = evaluateComputed(
      'FORMAT_DATE(DATE_ADD("2024-01-15T00:00:00Z", 2, "years"), "DD/MM/YYYY")',
      vals({}),
    );
    expect(result).toBe('15/01/2026');
  });

  it('arithmetic inside function arguments', () => {
    expect(evaluateComputed('ROUND(10 / 3, 2)', vals({}))).toBeCloseTo(3.33, 2);
  });

  it('CONCAT with arithmetic sub-expression', () => {
    const v = vals({ 'field::Qty': '5', 'field::Price': '20' });
    const result = evaluateComputed('CONCAT("Total: ", {{field::Qty}} * {{field::Price}})', v);
    expect(result).toBe('Total: 100');
  });
});

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

describe('error handling', () => {
  it('returns empty string for null/undefined expression', () => {
    expect(evaluateComputed(null, vals({}))).toBe('');
    expect(evaluateComputed(undefined, vals({}))).toBe('');
    expect(evaluateComputed('', vals({}))).toBe('');
  });

  it('returns empty string for unknown function', () => {
    expect(evaluateComputed('NOPE(1)', vals({}))).toBe('');
  });

  it('returns empty string for malformed expression', () => {
    expect(evaluateComputed('{{field::A} + 1', vals({}))).toBe('');
  });

  it('accepts a plain object as values map', () => {
    expect(evaluateComputed('{{field::X}} + 1', { 'field::X': '9' })).toBe(10);
  });
});

// ---------------------------------------------------------------------------
// extractTokens
// ---------------------------------------------------------------------------

describe('extractTokens', () => {
  it('extracts all token keys', () => {
    const tokens = extractTokens('{{field::A}} + {{serial.code}} * {{cf::abc}}');
    expect(tokens).toEqual(['field::A', 'serial.code', 'cf::abc']);
  });

  it('returns empty array for no tokens', () => {
    expect(extractTokens('2 + 3')).toEqual([]);
  });

  it('handles null/undefined', () => {
    expect(extractTokens(null)).toEqual([]);
    expect(extractTokens(undefined)).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// buildValuesMap
// ---------------------------------------------------------------------------

describe('buildValuesMap', () => {
  it('populates field:: keys from formModel', () => {
    const mockContext = {
      getPresetValue: () => undefined,
      getCustomFieldValue: () => undefined,
    };
    const map = buildValuesMap({ Qty: '10', Name: 'Widget' }, mockContext, []);
    expect(map.get('field::Qty')).toBe('10');
    expect(map.get('field::Name')).toBe('Widget');
  });

  it('resolves preset tokens lazily from context', () => {
    const mockContext = {
      getPresetValue: (key) => (key === 'serial.code' ? 'SN-001' : undefined),
      getCustomFieldValue: () => undefined,
    };
    const map = buildValuesMap({}, mockContext, []);
    expect(map.get('serial.code')).toBe('SN-001');
  });

  it('resolves cf:: tokens lazily from context', () => {
    const mockContext = {
      getPresetValue: () => undefined,
      getCustomFieldValue: (key) => (key === 'abc123' ? 'Red' : undefined),
    };
    const map = buildValuesMap({}, mockContext, []);
    expect(map.get('cf::abc123')).toBe('Red');
  });

  it('returns empty string for unknown tokens', () => {
    const mockContext = {
      getPresetValue: () => undefined,
      getCustomFieldValue: () => undefined,
    };
    const map = buildValuesMap({}, mockContext, []);
    expect(map.get('unknown.thing')).toBe('');
  });
});
