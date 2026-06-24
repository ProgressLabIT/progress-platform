/**
 * computedResolver.js
 *
 * Safe recursive-descent expression evaluator for computed print template fields.
 * No eval() — all evaluation goes through a hand-written parser.
 *
 * Token format: {{token}} where token is a field reference, preset, or custom field key.
 *   - {{field::FieldName}}  → sibling template field value
 *   - {{preset.key}}        → context preset value
 *   - {{cf::_key}}          → custom field value
 *
 * Supports:
 *   - Arithmetic: + - * / with standard precedence, parentheses, unary minus
 *   - Comparisons: == != < > <= >= (return boolean, for use with IF)
 *   - Auto-coercion: + does addition when both sides are numeric, concatenation otherwise
 *   - String literals in double quotes
 *   - Built-in functions (see FUNCTIONS map), including IF for conditional logic
 */

// ---------------------------------------------------------------------------
// Built-in functions
// ---------------------------------------------------------------------------

function toNum(v) {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
}

function toDate(v) {
  if (v instanceof Date) return v;
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return null;
  return d;
}

function pad(n, len = 2) {
  return String(n).padStart(len, '0');
}

function formatDate(dateStr, pattern) {
  const d = toDate(dateStr);
  if (!d) return '';
  return String(pattern)
    .replace('YYYY', String(d.getFullYear()))
    .replace('YY', String(d.getFullYear()).slice(-2))
    .replace('MM', pad(d.getMonth() + 1))
    .replace('DD', pad(d.getDate()))
    .replace('HH', pad(d.getHours()))
    .replace('mm', pad(d.getMinutes()))
    .replace('ss', pad(d.getSeconds()));
}

const FUNCTIONS = {
  // String
  CONCAT: (...args) => args.map(String).join(''),
  UPPER: (s) => String(s ?? '').toUpperCase(),
  LOWER: (s) => String(s ?? '').toLowerCase(),

  // Math
  ROUND: (n, decimals = 0) => {
    const factor = Math.pow(10, toNum(decimals));
    return Math.round(toNum(n) * factor) / factor;
  },
  ABS: (n) => Math.abs(toNum(n)),
  CEIL: (n) => Math.ceil(toNum(n)),
  FLOOR: (n) => Math.floor(toNum(n)),

  // Date
  FORMAT_DATE: formatDate,

  DAYS_BETWEEN: (d1, d2) => {
    const a = toDate(d1);
    const b = toDate(d2);
    if (!a || !b) return 0;
    const ms = Math.abs(a.getTime() - b.getTime());
    return Math.floor(ms / 86_400_000);
  },

  DATE_ADD: (dateStr, amount, unit) => {
    const d = toDate(dateStr);
    if (!d) return '';
    const n = toNum(amount);
    const u = String(unit ?? '').toLowerCase();
    const result = new Date(d.getTime());
    switch (u) {
      case 'years':   result.setFullYear(result.getFullYear() + n); break;
      case 'months':  result.setMonth(result.getMonth() + n); break;
      case 'days':    result.setDate(result.getDate() + n); break;
      case 'hours':   result.setHours(result.getHours() + n); break;
      case 'minutes': result.setMinutes(result.getMinutes() + n); break;
      default: break;
    }
    return result.toISOString();
  },

  YEAR:  (d) => { const dt = toDate(d); return dt ? dt.getFullYear() : 0; },
  MONTH: (d) => { const dt = toDate(d); return dt ? dt.getMonth() + 1 : 0; },
  DAY:   (d) => { const dt = toDate(d); return dt ? dt.getDate() : 0; },

  WEEK: (d) => {
    const dt = toDate(d);
    if (!dt) return 0;
    const target = new Date(Date.UTC(dt.getFullYear(), dt.getMonth(), dt.getDate()));
    target.setUTCDate(target.getUTCDate() + 4 - (target.getUTCDay() || 7));
    const yearStart = new Date(Date.UTC(target.getUTCFullYear(), 0, 1));
    return Math.ceil(((target - yearStart) / 86_400_000 + 1) / 7);
  },

  // Conditional
  IF: (condition, thenVal, elseVal) => {
    const truthy = condition !== false && condition !== 0 && condition !== '' && condition != null;
    return truthy ? thenVal : (elseVal ?? '');
  },

  // String
  SPLIT: (str, delimiter, index) => {
    const parts = String(str ?? '').split(String(delimiter ?? ','));
    const i = toNum(index);
    return i >= 0 && i < parts.length ? parts[i] : '';
  },

  // Date construction
  NOW: () => new Date().toISOString(),

  DATE: (fmt, ...parts) => {
    const mode = String(fmt ?? '').toUpperCase();
    switch (mode) {
      case 'YMD': {
        const [y, m, d] = parts.map(toNum);
        return new Date(Date.UTC(y, (m || 1) - 1, d || 1, 12)).toISOString();
      }
      case 'YM': {
        const [y, m] = parts.map(toNum);
        return new Date(Date.UTC(y, (m || 1) - 1, 1, 12)).toISOString();
      }
      case 'Y': {
        const y = toNum(parts[0]);
        return new Date(Date.UTC(y, 0, 1, 12)).toISOString();
      }
      case 'YW': {
        const y = toNum(parts[0]);
        const w = toNum(parts[1]);
        // ISO 8601: week 1 contains January 4th. Monday of week w:
        const jan4 = new Date(Date.UTC(y, 0, 4, 12));
        const dayOfWeek = jan4.getUTCDay() || 7; // Mon=1..Sun=7
        const mondayW1 = new Date(jan4.getTime() - (dayOfWeek - 1) * 86_400_000);
        const target = new Date(mondayW1.getTime() + (w - 1) * 7 * 86_400_000);
        return target.toISOString();
      }
      default:
        return '';
    }
  },
};

// ---------------------------------------------------------------------------
// Tokenizer
// ---------------------------------------------------------------------------

const TT = Object.freeze({
  NUMBER: 'NUMBER',
  STRING: 'STRING',
  TOKEN: 'TOKEN',       // {{...}}
  IDENT: 'IDENT',       // function name
  PLUS: '+',
  MINUS: '-',
  STAR: '*',
  SLASH: '/',
  LPAREN: '(',
  RPAREN: ')',
  COMMA: ',',
  EQ: '==',
  NEQ: '!=',
  LTE: '<=',
  GTE: '>=',
  LT: '<',
  GT: '>',
  EOF: 'EOF',
});

function tokenize(expr) {
  const tokens = [];
  let i = 0;
  const src = expr;

  while (i < src.length) {
    // Whitespace
    if (/\s/.test(src[i])) { i++; continue; }

    // {{...}} token
    if (src[i] === '{' && src[i + 1] === '{') {
      const end = src.indexOf('}}', i + 2);
      if (end === -1) throw new Error(`Unterminated token at position ${i}`);
      const content = src.slice(i + 2, end).trim();
      tokens.push({ type: TT.TOKEN, value: content });
      i = end + 2;
      continue;
    }

    // Number (integer or decimal)
    if (/[0-9]/.test(src[i]) || (src[i] === '.' && i + 1 < src.length && /[0-9]/.test(src[i + 1]))) {
      let num = '';
      while (i < src.length && /[0-9.]/.test(src[i])) { num += src[i]; i++; }
      tokens.push({ type: TT.NUMBER, value: parseFloat(num) });
      continue;
    }

    // Double-quoted string
    if (src[i] === '"') {
      let str = '';
      i++; // skip opening quote
      while (i < src.length && src[i] !== '"') {
        if (src[i] === '\\' && i + 1 < src.length) { str += src[i + 1]; i += 2; }
        else { str += src[i]; i++; }
      }
      if (i >= src.length) throw new Error('Unterminated string literal');
      i++; // skip closing quote
      tokens.push({ type: TT.STRING, value: str });
      continue;
    }

    // Identifier (function name): A-Z, a-z, _
    if (/[A-Za-z_]/.test(src[i])) {
      let id = '';
      while (i < src.length && /[A-Za-z0-9_]/.test(src[i])) { id += src[i]; i++; }
      tokens.push({ type: TT.IDENT, value: id });
      continue;
    }

    // Two-char comparison operators (must check before single-char)
    if (src[i] === '=' && src[i + 1] === '=') { tokens.push({ type: TT.EQ, value: '==' }); i += 2; continue; }
    if (src[i] === '!' && src[i + 1] === '=') { tokens.push({ type: TT.NEQ, value: '!=' }); i += 2; continue; }
    if (src[i] === '<' && src[i + 1] === '=') { tokens.push({ type: TT.LTE, value: '<=' }); i += 2; continue; }
    if (src[i] === '>' && src[i + 1] === '=') { tokens.push({ type: TT.GTE, value: '>=' }); i += 2; continue; }
    if (src[i] === '<') { tokens.push({ type: TT.LT, value: '<' }); i++; continue; }
    if (src[i] === '>') { tokens.push({ type: TT.GT, value: '>' }); i++; continue; }

    // Single-char operators
    const charMap = { '+': TT.PLUS, '-': TT.MINUS, '*': TT.STAR, '/': TT.SLASH, '(': TT.LPAREN, ')': TT.RPAREN, ',': TT.COMMA };
    if (charMap[src[i]]) {
      tokens.push({ type: charMap[src[i]], value: src[i] });
      i++;
      continue;
    }

    throw new Error(`Unexpected character '${src[i]}' at position ${i}`);
  }

  tokens.push({ type: TT.EOF, value: null });
  return tokens;
}

// ---------------------------------------------------------------------------
// Parser + Evaluator (recursive descent, evaluates during parse)
// ---------------------------------------------------------------------------

function createParser(tokens, valuesMap) {
  let pos = 0;

  function peek() { return tokens[pos]; }
  function advance() { return tokens[pos++]; }
  function expect(type) {
    const t = advance();
    if (t.type !== type) throw new Error(`Expected ${type} but got ${t.type} ('${t.value}')`);
    return t;
  }

  function resolveToken(content) {
    if (valuesMap.has(content)) return valuesMap.get(content);
    return '';
  }

  const COMPARISON_OPS = new Set([TT.EQ, TT.NEQ, TT.LT, TT.GT, TT.LTE, TT.GTE]);

  // Expression = Additive ((== | != | < | > | <= | >=) Additive)?
  function parseExpression() {
    let left = parseAdditive();
    if (COMPARISON_OPS.has(peek().type)) {
      const op = advance().type;
      const right = parseAdditive();
      switch (op) {
        // eslint-disable-next-line eqeqeq
        case TT.EQ:  return left == right;
        // eslint-disable-next-line eqeqeq
        case TT.NEQ: return left != right;
        case TT.LT:  return toNum(left) <  toNum(right);
        case TT.GT:  return toNum(left) >  toNum(right);
        case TT.LTE: return toNum(left) <= toNum(right);
        case TT.GTE: return toNum(left) >= toNum(right);
      }
    }
    return left;
  }

  // Additive = Term (('+' | '-') Term)*
  function parseAdditive() {
    let left = parseTerm();
    while (peek().type === TT.PLUS || peek().type === TT.MINUS) {
      const op = advance().type;
      const right = parseTerm();
      if (op === TT.PLUS) {
        if (isNumericValue(left) && isNumericValue(right)) {
          left = Number(left) + Number(right);
        } else {
          left = String(left ?? '') + String(right ?? '');
        }
      } else {
        left = toNum(left) - toNum(right);
      }
    }
    return left;
  }

  // Term = Unary (('*' | '/') Unary)*
  function parseTerm() {
    let left = parseUnary();
    while (peek().type === TT.STAR || peek().type === TT.SLASH) {
      const op = advance().type;
      const right = parseUnary();
      if (op === TT.STAR) left = toNum(left) * toNum(right);
      else {
        const divisor = toNum(right);
        left = divisor === 0 ? 0 : toNum(left) / divisor;
      }
    }
    return left;
  }

  // Unary = '-' Unary | Primary
  function parseUnary() {
    if (peek().type === TT.MINUS) {
      advance();
      return -toNum(parseUnary());
    }
    return parsePrimary();
  }

  // Primary = NUMBER | STRING | TOKEN | FunctionCall | '(' Expression ')'
  function parsePrimary() {
    const t = peek();

    if (t.type === TT.NUMBER) {
      advance();
      return t.value;
    }

    if (t.type === TT.STRING) {
      advance();
      return t.value;
    }

    if (t.type === TT.TOKEN) {
      advance();
      return resolveToken(t.value);
    }

    if (t.type === TT.IDENT) {
      return parseFunctionCall();
    }

    if (t.type === TT.LPAREN) {
      advance();
      const val = parseExpression();
      expect(TT.RPAREN);
      return val;
    }

    throw new Error(`Unexpected token ${t.type} ('${t.value}')`);
  }

  // FunctionCall = IDENT '(' (Expression (',' Expression)*)? ')'
  function parseFunctionCall() {
    const name = advance().value;
    expect(TT.LPAREN);
    const args = [];
    if (peek().type !== TT.RPAREN) {
      args.push(parseExpression());
      while (peek().type === TT.COMMA) {
        advance();
        args.push(parseExpression());
      }
    }
    expect(TT.RPAREN);

    const fn = FUNCTIONS[name];
    if (!fn) throw new Error(`Unknown function: ${name}`);
    return fn(...args);
  }

  return { parseExpression };
}

function isNumericValue(v) {
  if (typeof v === 'number') return true;
  if (typeof v === 'string' && v.trim() !== '' && Number.isFinite(Number(v))) return true;
  return false;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Evaluate a computed expression.
 *
 * @param {string} expression - The formula (e.g. '{{field::Qty}} * 2')
 * @param {Map<string, string> | Record<string, string>} valuesMap
 *   Maps token content to resolved string values.
 *   Keys are the raw token content without braces, e.g.:
 *     'field::Quantity', 'serial.code', 'cf::abc123'
 * @returns {string|number} The evaluated result
 */
export function evaluateComputed(expression, valuesMap) {
  if (!expression || typeof expression !== 'string') return '';
  const map = valuesMap instanceof Map ? valuesMap : new Map(Object.entries(valuesMap ?? {}));
  try {
    const tokens = tokenize(expression.trim());
    const parser = createParser(tokens, map);
    const result = parser.parseExpression();
    return result;
  } catch (e) {
    console.warn(`[computedResolver] Error evaluating "${expression}":`, e.message);
    return '';
  }
}

/**
 * Extract all {{...}} token keys from an expression.
 * Useful for dependency analysis (which fields does a computed expression reference?).
 *
 * @param {string} expression
 * @returns {string[]} Array of token content strings (e.g. ['field::Qty', 'serial.code'])
 */
export function extractTokens(expression) {
  if (!expression) return [];
  const regex = /\{\{\s*([\w:.]+(?:\s+[\w:.]+)*)\s*\}\}/g;
  const tokens = [];
  let match;
  while ((match = regex.exec(expression)) !== null) {
    tokens.push(match[1]);
  }
  return tokens;
}

/**
 * Build a values map for evaluateComputed from the current form model and context.
 *
 * @param {Record<string, string>} formModel - Current form field values (reactive)
 * @param {{ getPresetValue(key: string): string|undefined, getCustomFieldValue(key: string): string|undefined }} context
 * @param {Array<{ _key: string }>} customFields
 * @returns {Map<string, string>}
 */
export function buildValuesMap(formModel, context, customFields) {
  const map = new Map();

  // Add all form fields as field:: references
  if (formModel) {
    for (const [key, value] of Object.entries(formModel)) {
      map.set(`field::${key}`, String(value ?? ''));
    }
  }

  // Preset and custom field tokens are resolved on-demand via a Proxy-like approach,
  // but since Map is simpler, we pre-populate known presets isn't feasible (too many).
  // Instead, we return a special Map subclass that resolves on .get().
  return new LazyValuesMap(map, context);
}

/**
 * Map subclass that resolves preset and cf:: tokens lazily from context.
 * Field:: tokens are pre-populated; everything else hits context on first access.
 */
class LazyValuesMap extends Map {
  /** @type {{ getPresetValue: Function, getCustomFieldValue: Function } | null} */
  _context;

  constructor(base, context) {
    super(base);
    this._context = context;
  }

  get(key) {
    if (super.has(key)) return super.get(key);

    if (!this._context) return '';

    let resolved;
    if (key.startsWith('cf::')) {
      const cfKey = key.slice(4);
      resolved = this._context.getCustomFieldValue(cfKey);
    } else if (key.startsWith('field::')) {
      // Field not in form model — return empty
      resolved = '';
    } else {
      // Treat as preset. Canonical token is {{preset.key}}; strip the prefix so it
      // matches getPresetValue's bare keys (bare {{serial.code}} tokens still resolve).
      const presetKey = key.startsWith('preset.') ? key.slice(7) : key;
      resolved = this._context.getPresetValue(presetKey);
    }

    const value = String(resolved ?? '');
    super.set(key, value); // cache for subsequent accesses
    return value;
  }

  has(key) {
    return true; // all keys are resolvable (missing → empty string)
  }
}
