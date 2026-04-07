/**
 * templateResolver.js
 *
 * Pure-logic encode/decode/resolve trio for template string expressions.
 * No framework dependencies — plain ES module.
 *
 * Token format: {{token}} where token contains word chars, colons, dots,
 * and optionally spaces (for field names like {{field::Data Code}}).
 * Custom field tokens: {{cf::_key}} (encoded) / {{cf::slug}} (decoded)
 * Field ref tokens: {{field::FieldName}} (resolved from sibling form values)
 * Preset tokens: {{preset.key}} (unchanged through encode/decode)
 */

const TOKEN_REGEX = /\{\{\s*([\w:.]+(?:\s+[\w:.]+)*)\s*\}\}/g;

/**
 * slugify(name) -> string
 * Converts a human label into a stable snake_case identifier.
 *
 * @param {string} name
 * @returns {string}
 */
export function slugify(name) {
  return name
    .toLowerCase()
    .replace(/\([^)]*\)/g, '')        // remove parenthesised content
    .replace(/[^a-z0-9]+/g, '_')      // non-alphanumeric runs → '_'
    .replace(/_+/g, '_')              // collapse consecutive underscores
    .replace(/^_|_$/g, '');           // trim leading/trailing underscores
}

/**
 * encodeExpression(expr, customFields) -> string
 * Replaces {{cf::slug}} tokens with {{cf::_key}} for storage.
 * Preset tokens pass through unchanged.
 *
 * @param {string | null | undefined} expr
 * @param {Array<{ _key: string; name: string }>} customFields
 * @returns {string}
 */
export function encodeExpression(expr, customFields) {
  if (expr == null) return '';
  const slugToKey = Object.fromEntries(
    customFields.map((cf) => [slugify(cf.name), cf._key])
  );
  return expr.replace(TOKEN_REGEX, (_match, token) => {
    if (token.startsWith('cf::')) {
      const slug = token.slice(4);
      const key = slugToKey[slug];
      return key != null ? `{{cf::${key}}}` : _match;
    }
    return `{{${token}}}`;
  });
}

/**
 * decodeExpression(expr, customFields) -> string
 * Replaces {{cf::_key}} tokens with {{cf::slug}} for display/editing.
 * Preset tokens pass through unchanged.
 *
 * @param {string | null | undefined} expr
 * @param {Array<{ _key: string; name: string }>} customFields
 * @returns {string}
 */
export function decodeExpression(expr, customFields) {
  if (expr == null) return '';
  const keyToSlug = Object.fromEntries(
    customFields.map((cf) => [cf._key, slugify(cf.name)])
  );
  return expr.replace(TOKEN_REGEX, (_match, token) => {
    if (token.startsWith('cf::')) {
      const key = token.slice(4);
      const slug = keyToSlug[key];
      return slug != null ? `{{cf::${slug}}}` : _match;
    }
    return `{{${token}}}`;
  });
}

/**
 * resolveExpression(expr, context, customFields, formModel?) -> string
 * Resolves all tokens to their runtime values.
 * Field ref tokens ({{field::Name}}) use formModel values.
 * Custom field tokens use context.getCustomFieldValue(_key).
 * Preset tokens use context.getPresetValue(key).
 * Missing values resolve to empty string.
 *
 * @param {string | null | undefined} expr
 * @param {{ getPresetValue(key: string): string | undefined; getCustomFieldValue(key: string): string | undefined }} context
 * @param {Array<{ _key: string }>} customFields
 * @param {Record<string, string> | null | undefined} [formModel] - Sibling field values for {{field::Name}} tokens
 * @returns {string}
 */
export function resolveExpression(expr, context, customFields, formModel) {
  if (expr == null) return '';
  return expr.replace(TOKEN_REGEX, (_match, token) => {
    if (token.startsWith('field::')) {
      const fieldName = token.slice(7);
      return String(formModel?.[fieldName] ?? '');
    }
    if (token.startsWith('cf::')) {
      const key = token.slice(4);
      return String(context.getCustomFieldValue(key) ?? '');
    }
    return String(context.getPresetValue(token) ?? '');
  });
}
