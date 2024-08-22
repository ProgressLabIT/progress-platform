from datetime import datetime
from commons.utils.db import db

COUNTER_TICK = """
// Get current counter value
let c = DOCUMENT(Counter, @counter_key)

// Reset counter if needed (Beginning of year)
let reset_counter = DATE_NOW() > DATE_TIMESTAMP(c.reset_date)

// Increment tick and reset_date (if needed)
let next_tick = reset_counter ? 2 : c.next_tick + 1
let reset_date = reset_counter ? DATE_ADD(c.reset_date, 1, c.frequency) : c.reset_date
update c with { reset_date, next_tick } in Counter

// Return the counter value prior to update
RETURN c
"""

def compute_counter(counter):
  counter_elements = []
  now = datetime.now()
  for token in counter['template']:
    if token.startswith('%'):
      # datetime element: e.g. '%y' === '23'
      counter_elements.append(now.strftime(token))
    elif token.startswith('#'):
      # counter number of digits: e.g. '#5' ---> 00013
      digits = int(token[1:])
      counter_elements.append(str(counter['next_tick']).zfill(digits))
    else:
      # Fixed text: append token as is
      counter_elements.append(token)

  return ''.join(counter_elements)

def _generate_counter(tx, counter_key):
  return compute_counter(tx.aql.execute(COUNTER_TICK, bind_vars={ 'counter_key': counter_key }).next())

