from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Self
import uuid

from arango.database import TransactionDatabase
from pydantic import BaseModel, model_validator, Field

from utils.event import get_event_class
from models.event import EventType, EventModel, EventInfoModel
from utils.db import db
from utils.dt import timestamp

class BaseEvent(ABC):
  """
  Base class for all events.
  """
  @classmethod
  @abstractmethod
  def get_event_type(cls) -> EventType:
    """
    Returns the event type. Must be implemented by the subclass.
    """
    pass

  @property
  @abstractmethod
  def tx_collections(self) -> list[str]:
    """
    Returns the collections that should be used for the transaction. Must be implemented by the subclass.
    """
    pass

  @abstractmethod
  def apply(self):
    """
    Apply updates to global application state based on specific event.
    Any data that must be returned to the caller must be stored in the `response` property.
    """
    pass

  @classmethod
  def get_event_model(cls) -> type[BaseModel]:
    """
    Returns the event model used to validate event data. Must be implemented by the subclass,
    defining an InfoModel class that inherits from EventInfoModel.
    """
    return cls.InfoModel

  @classmethod
  def create_as_child(cls, context: EventModel, new_event_data: 'cls.InfoModel') -> Self:
    """
    Create a child event from an existing event.
    """
    info = context.info.model_dump()
    info['primary'] = False
    info.update(new_event_data)
    new_event = cls(tx = context.tx, info = info)
    new_event.save()
    return new_event.response


  @property
  def event_first(self) -> bool:
    """
    Can be overridden by subclasses to determine if the event must be stored in the database before being processed.
    """
    # TODO: Consider always storing events in the database first, and then processing them to remove the need for this property and dual logic
    return False

  def __init__(self, info, tx: TransactionDatabase | None = None):
    self.tx = tx
    self.response = None

    # Validate general event properties
    has_tx_or_event_group = tx is not None or info['event_group'] is not None
    has_tx_and_event_group = tx is not None and info['event_group'] is not None

    if (info['primary'] and has_tx_or_event_group):
      raise ValueError('Primary events cannot be initialized with existing transaction or event group')

    if not info['primary'] and not has_tx_and_event_group:
      raise ValueError('Secondary events cannot be initialized without a transaction and event group')

    # Validate and store event specific data. Will raise ValueError if validation fails
    self.info = self.get_event_model()(**info)


  def store_event(self):
    """
    Store the event in the database.
    """
    record = self.info.model_dump()
    # update with data modified through the apply method
    if hasattr(self, 'event_key'):
      record.update(dict(_key=self.event_key))

    self.event_key = self.tx.collection('Event').insert(record, overwrite=True)['_key']

  def save(self):
    """
    Save the event to the database and handle transaction.
    """
    collections = self.tx_collections + ['Event']

    try:
      if self.info.primary:
        self.tx = db.begin_transaction(write=collections)
        self.info.event_group = str(uuid.uuid4())

      if self.event_first:
        self.store_event()

      # Apply updates to global application state based on specific event
      self.apply()

      # Re-save event with new data added
      self.store_event()

      # Commit transaction
      if self.info.primary:
        self.tx.commit_transaction()

      # Return any required value
      return self.response

    # In case of exceptions abort transaction without catching them if transaction is still open
    finally:
      if self.info.primary and self.tx.transaction_status() == 'running': # See transaction statuses in the HTTP API of ArangoDB
        self.tx.abort_transaction()
