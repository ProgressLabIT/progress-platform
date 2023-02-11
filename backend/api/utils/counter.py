from datetime import datetime

COUNTER_TICK = """
// Get counter configuration
let c = DOCUMENT(Config, 'counters')[@counter_name]

// Return config (template and next_tick) and increment tick
let new = MERGE(c, { next_tick: c.next_tick + 1 })
update 'counters' with { @counter_name: new } in Config
RETURN c
"""

def generate_counter(tx, counter_name):
  c = tx.aql.execute(COUNTER_TICK, bind_vars={ 'counter_name': counter_name }).next()
  counter_elements = []
  now = datetime.now()
  for token in c['template']:
    if token.startswith('%'):
      # datetime element: e.g. '%y' === '23'
      counter_elements.append(now.strftime(token))
    elif token.startswith('#'):
      # counter number of digits: e.g. '#5' ---> 00013
      digits = int(token[1:])
      counter_elements.append(str(c['next_tick']).zfill(digits))
    else:
      # Fixed text: append token as is
      counter_elements.append(token)

  return ''.join(counter_elements)
