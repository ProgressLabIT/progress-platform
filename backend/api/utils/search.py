import re

def wildcard_to_regex(search_string: str) -> str:
  """
  Convert a wildcard search string to a regex pattern.

  Wildcards:
    * = one or more characters
    ? = any single character

  Escape sequences:
    \* = literal asterisk
    \? = literal question mark

  Examples:
    "product*"     -> matches "product123", "productABC"
    "product\*"    -> matches literal "product*"
    "test?.txt"    -> matches "test1.txt", "testA.txt"
    "test\?.txt"   -> matches literal "test?.txt"
  """
  if search_string is None:
    return None

  # Store whether string starts/ends with wildcard for anchor logic
  starts_with_wildcard = search_string.startswith('*')
  ends_with_wildcard = search_string.endswith('*')

  # Temporarily replace escaped wildcards with unique placeholders
  LITERAL_ASTERISK = '<<LITERAL_ASTERISK>>'
  LITERAL_QUESTION = '<<LITERAL_QUESTION>>'

  search_string = search_string.replace(r'\*', LITERAL_ASTERISK)
  search_string = search_string.replace(r'\?', LITERAL_QUESTION)

  # Escape all regex special characters (including remaining unescaped * and ?)
  escaped = re.escape(search_string)

  # Replace escaped wildcards with regex patterns
  # \* becomes .+ (one or more characters)
  # \? becomes . (any single character)
  regex_pattern = escaped.replace(r'\*', '.*').replace(r'\?', '.')

  # Restore literal wildcards by replacing placeholders with escaped versions
  regex_pattern = regex_pattern.replace(re.escape(LITERAL_ASTERISK), r'\*')
  regex_pattern = regex_pattern.replace(re.escape(LITERAL_QUESTION), r'\?')

  if starts_with_wildcard:
    regex_pattern = f'{regex_pattern}$'

  if ends_with_wildcard:
    regex_pattern = f'^{regex_pattern}'

  return regex_pattern
