/**
 * Composable to convert wildcard search strings to regex patterns.
 *
 * Wildcards:
 *   * = one or more characters
 *   ? = any single character
 *
 * Escape sequences:
 *   \* = literal asterisk
 *   \? = literal question mark
 *
 * Examples:
 *   "product*"     -> matches "product123", "productABC"
 *   "product\*"    -> matches literal "product*"
 *   "test?.txt"    -> matches "test1.txt", "testA.txt"
 *   "test\?.txt"   -> matches literal "test?.txt"
 *
 * @returns {Object} - Object containing the wildcardToRegex function
 */
export function useWildcardToRegex() {
  /**
   * Convert a wildcard search string to a regex pattern.
   *
   * @param {string|null} searchString - The wildcard string to convert
   * @returns {RegExp|null} - The regex pattern, or null if input is null
   */
  const wildcardToRegex = (searchString) => {
    if (searchString === null || searchString === undefined) {
      return null;
    }

    // Store whether string starts/ends with wildcard for anchor logic
    const startsWithWildcard = searchString.startsWith('*');
    const endsWithWildcard = searchString.endsWith('*');

    // Temporarily replace escaped wildcards with unique placeholders
    const LITERAL_ASTERISK = '<<LITERAL_ASTERISK>>';
    const LITERAL_QUESTION = '<<LITERAL_QUESTION>>';

    let processedString = searchString.replace(/\\\*/g, LITERAL_ASTERISK);
    processedString = processedString.replace(/\\\?/g, LITERAL_QUESTION);

    // Escape all regex special characters (including remaining unescaped * and ?)
    // This matches Python's re.escape behavior
    const escaped = processedString.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    // Replace escaped wildcards with regex patterns
    // \* becomes .* (one or more characters)
    // \? becomes . (any single character)
    let regexPattern = escaped.replace(/\\\*/g, '.*').replace(/\\\?/g, '.');

    // Restore literal wildcards by replacing placeholders with escaped versions
    // Need to escape the placeholders first (like Python's re.escape)
    const escapedAsteriskPlaceholder = LITERAL_ASTERISK.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const escapedQuestionPlaceholder = LITERAL_QUESTION.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    regexPattern = regexPattern.replace(new RegExp(escapedAsteriskPlaceholder, 'g'), '\\*');
    regexPattern = regexPattern.replace(new RegExp(escapedQuestionPlaceholder, 'g'), '\\?');

    if (startsWithWildcard) {
      regexPattern = `${regexPattern}$`;
    }

    if (endsWithWildcard) {
      regexPattern = `^${regexPattern}`;
    }

    return new RegExp(regexPattern, 'i');
  };

  return {
    wildcardToRegex,
  };
}

