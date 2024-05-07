from events import (
  CollaborationEvent,
  ProductionActivityEvent,
  ProductionAdminEvent,
  SharedEventMethods,
)
from models.event import EventModel
from commons.utils.db import db


class Event(
  CollaborationEvent,
  ProductionActivityEvent,
  ProductionAdminEvent,
  SharedEventMethods
  ):
  """
  This class serves as collector of all event categories and as main "entrypoint" for the event API
  It abstracts the general logic of processing and saving events from the specifics defined in each
  of the classes it inherits from.

  Each inherited class includes a property named after each event type of its "category".
  Each event type (class property) is itself an EventMeta class instance which defines:
  - the list of collections to use in the transaction
  - the actions to be carried out specific to the event type
  """
  ######################################################################
  # INIT & SAVE
  ######################################################################

  def __init__(self, event: EventModel, database=db):
    self.db = database
    self.info = event
    self.meta = getattr(self, self.info.event_type.value)
    self.response = None

    # define action to be taken based on the event type
    self.action = getattr(self, self.meta.action)

  def save(self):
    # Initialize transaction
    self.meta.collections.append('Event')
    self.tx = self.db.begin_transaction(write=self.meta.collections)

    try:
      # Save event, storing its key for later use
      if self.meta.event_first:
        event_record = self.tx.collection('Event').insert(self.info, return_new=True)['new']
        self.info = EventModel(**event_record)

      # Apply updates to global application state based on specific event
      self.action()

      # Apply updates based on event category shared logic
      for method in self.meta.post_processing or []:
        getattr(self, method)()

      # Re-save event with new data added
      self.tx.collection('Event').insert(self.info, overwrite=True)

      # Commit transaction
      self.tx.commit_transaction()

      # Return any required value
      return self.response

    # In case of exceptions, abort transaction without catching them
    finally:
      if self.tx.transaction_status() != 'committed':
        self.tx.abort_transaction()


