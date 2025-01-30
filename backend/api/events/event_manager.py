from events.base_event import BaseEvent
from events.event_model import EventModel
from events.event_type import EventType
from events.serial.serial_created import SerialCreated
from utils.db import db
from typing import Any
import traceback

import uuid


class EventManager:

    @staticmethod
    def factory(classname, data: Any = None):
      module = __import__("events")
      class_ = getattr(module, classname)
      event = object.__new__(class_)
      event.set_model(data)
      return event

    @staticmethod
    def create_event(event_data: EventModel):
       if hasattr(event_data, 'event_type') and event_data.event_type in EventType.__members__:
         event = EventManager.factory(EventType[event_data.event_type].value.class_name, event_data)
         return event
       raise ValueError("Invalid event type")

    @staticmethod
    def send_event(event_data: EventModel, tx = None):
        event = EventManager.create_event(event_data)

        collections = event.get_write_collections()

        # Initialize transaction
        event.set_transaction(tx if tx is not None else  db.begin_transaction(write=collections))

        # Define event UUID
        event.event_data.event_group = str(uuid.uuid4())

        try:
          response = EventManager.handle_event(event)
          response['child_responses'] = event.child_responses
          # Commit transaction
          event.tx.commit_transaction()
          # Return any required value
          return response

        # In case of exceptions, abort transaction without catching them
        finally:
          if event.tx.transaction_status() != 'committed':
            event.tx.abort_transaction()

    @staticmethod
    def handle_event(event):
      event_key = None
      # Save event, storing its key for later use
      if event.is_event_first():
        event_key = event.tx.collection('Event').insert(event.event_data, return_new=True)['new']['_key']

      if event.validate_event():
        # Apply updates to global application state based on specific event
        event.apply()
        # Apply updates based on event category shared logic
        event.post_processing()
        # Re-save event with new data added
        event_key = event.tx.collection('Event').insert(event.event_data, overwrite=True, return_new=True)['new']['_key']

      response = event.get_response()

      if event_key is not None:
        response['event_key'] = event_key

      response['managed_event_type'] = event.event_data.event_type
      return response

    @staticmethod
    def notify_event(origin: BaseEvent, event_model: EventModel):
      event_model.user_key = origin.event_data.user_key
      event_model.event_group = origin.event_data.event_group
      event_model.timestamp = origin.event_data.timestamp
      event_model.user_session_key = origin.event_data.user_session_key

      event = EventManager.create_event(event_model)


      event.set_response(dict())
      # Initialize transaction
      event.set_transaction(origin.tx)

      response = EventManager.handle_event(event)
      origin.child_responses.append(response)
      # Return any required value
      return response



