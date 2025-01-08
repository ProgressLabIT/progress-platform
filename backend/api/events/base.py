from models.event import EventModel
from abc import ABC, abstractmethod
from arango.database import StandardDatabase, TransactionDatabase

from models.event import EventModel
from utils.db import db
import uuid

class BaseEvent (ABC):
  db: StandardDatabase
  tx: TransactionDatabase
  info: EventModel
  response: int | str | dict | list

  def __init__(self,  database=db, tx=None):
    self.db = database
    self.response = None

  @abstractmethod
  def can_handle(self, event: EventModel) -> bool:
    pass

  def define_action(self, event_type: str):
    try:
      self.meta = getattr(self, event_type)
      # define action to be taken based on the event type
      self.action = getattr(self, self.meta.action)
    except AttributeError:
      self.action = None

  def apply(self, tx=None):
    if not self.can_handle():
      return

    # Initialize transaction
    self.meta.collections.append('Event')

    self.tx = tx if tx is not None else self.db.begin_transaction(write=self.meta.collections)

    # Define event UUID
    if self.info.event_group is None:
      self.info.event_group = str(uuid.uuid4())

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
      if self.info.primary:
        self.tx.commit_transaction()

      # Return any required value
      return self.response

    # In case of exceptions, abort transaction without catching them
    finally:
      if self.tx.transaction_status() != 'committed' and self.info.primary:
        self.tx.abort_transaction()
