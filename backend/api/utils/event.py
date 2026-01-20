from models.event import EventType

_event_map = {
  # Events will register into this dictionary as they are parsed by the python interpreter
}

def register_event_class(event_type: EventType, event_class):
  _event_map[event_type] = event_class

def get_event_class(event_type: EventType):
  try:
    return _event_map[event_type]
  except KeyError:
    raise ValueError(f'Event type {event_type.value} not found')
