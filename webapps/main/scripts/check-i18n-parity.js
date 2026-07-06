/**
 * check-i18n-parity.js
 *
 * Dependency-free ESM script that compares the key sets of en.js and it.js
 * locale files in src/i18n/. Exits 0 when both sets match, 1 when they differ.
 * Prints a grouped report of missing keys per locale on mismatch.
 *
 * Usage: node scripts/check-i18n-parity.js
 *        yarn i18n:check
 */

const enUrl = new URL('../src/i18n/en.js', import.meta.url);
const itUrl = new URL('../src/i18n/it.js', import.meta.url);

const enModule = await import(enUrl.href);
const itModule = await import(itUrl.href);

const enObj = enModule.default;
const itObj = itModule.default;

/**
 * Recursively collect all dotted key paths from a nested object.
 * Arrays are treated as leaf values (not recursed into).
 * Numeric keys (e.g. 404) are included as-is in the path.
 *
 * @param {object} obj
 * @param {string} prefix
 * @param {Set<string>} result
 * @returns {Set<string>}
 */
function collectKeys(obj, prefix = '', result = new Set()) {
  for (const [key, value] of Object.entries(obj)) {
    const path = prefix ? `${prefix}.${key}` : String(key);
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      collectKeys(value, path, result);
    } else {
      result.add(path);
    }
  }
  return result;
}

const enKeys = collectKeys(enObj);
const itKeys = collectKeys(itObj);

const missingFromIt = [...enKeys].filter((k) => !itKeys.has(k)).sort();
const missingFromEn = [...itKeys].filter((k) => !enKeys.has(k)).sort();

const totalMatch = enKeys.size - missingFromIt.length;

if (missingFromIt.length === 0 && missingFromEn.length === 0) {
  console.log(`i18n parity OK — ${enKeys.size} keys match`);
  process.exit(0);
}

// Report mismatch
if (missingFromIt.length > 0) {
  console.log(`\nMissing from it.js (${missingFromIt.length} keys):`);
  for (const key of missingFromIt) {
    console.log(`  ${key}`);
  }
}

if (missingFromEn.length > 0) {
  console.log(`\nMissing from en.js (${missingFromEn.length} keys):`);
  for (const key of missingFromEn) {
    console.log(`  ${key}`);
  }
}

console.log(
  `\nSummary: ${missingFromIt.length} key(s) missing from it.js, ${missingFromEn.length} key(s) missing from en.js` +
    ` (${totalMatch} keys common to both)`
);

process.exit(1);
