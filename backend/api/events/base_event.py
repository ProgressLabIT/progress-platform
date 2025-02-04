from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Self
import uuid

from arango.database import TransactionDatabase
from pydantic import BaseModel, model_validator, Field

from utils.event import get_event_class
from models.event import EventType, EventModel, EventInfo
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
    defining an EventModel class that inherits from EventInfo.
    """
    return cls.InfoModel

  @classmethod
  def create_as_child(cls, context: EventModel, new_event_data: 'cls.InfoModel', description: str | None = None) -> Self:
    """
    Create a child event from an existing event.
    """
    new_event = cls(EventModel(
      primary = False,
      event_group = context.event_group,
      tx = context.tx,
      user_key = context.event_data.user_key,
      user_session_key = context.event_data.user_session_key,
      timestamp = context.event_data.timestamp,
      info = new_event_data,
      description = description,
      event_type = cls.get_event_type()
    ))
    new_event.save()
    return new_event.response


  @property
  def event_first(self) -> bool:
    """
    Can be overridden by subclasses to determine if the event must be stored in the database before being processed.
    """
    # TODO: Consider always storing events in the database first, and then processing them to remove the need for this property and dual logic
    return False

  def __init__(self, event_data: EventModel):
    self.primary = event_data.primary
    self.event_group = event_data.event_group
    self.tx = event_data.tx
    self.event_data = event_data # data to be stored in the database
    self.event_data.event_type = self.get_event_type()

    # Validate general event properties
    has_tx_or_event_group = self.tx is not None or self.event_group is not None
    has_tx_and_event_group = self.tx is not None and self.event_group is not None

    if (self.primary and has_tx_or_event_group):
      raise ValueError('Primary events cannot be initialized with existing transaction or event group')

    if not self.primary and not has_tx_and_event_group:
      raise ValueError('Secondary events cannot be initialized without a transaction and event group')

    # Validate and store event specific data. Will raise ValueError if validation fails
    self.info = self.get_event_model()(**event_data.info.model_dump())


  def store_event(self):
    """
    Store the event in the database.
    """
    record = self.event_data.model_dump()
    record.update(dict(info=self.info.model_dump()))
    # update with data modified through the apply method
    if self.event_key:
      record.update(dict(_key=self.event_key))

    self.event_key = self.tx.collection('Event').insert(record, overwrite=True)['_key']

  def save(self):
    """
    Save the event to the database and handle transaction.
    """
    try:
      if self.primary:
        self.tx = db.begin_transaction(write=self.tx_collections)
        self.event_group = str(uuid.uuid4())

      if self.event_first:
        self.store_event()

      # Apply updates to global application state based on specific event
      self.apply()

      # Re-save event with new data added
      self.store_event()

      # Commit transaction
      self.tx.commit_transaction()

    # In case of exceptions abort transaction without catching them if transaction is still open
    finally:
      if self.tx.transaction_status() == 'running': # See transaction statuses in the HTTP API of ArangoDB
        self.tx.abort_transaction()
