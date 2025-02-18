import uuid
from abc import ABC, abstractmethod
from typing import Self

from arango.database import TransactionDatabase
from models.event import EventInfoModel, EventType
from pydantic import BaseModel
from utils.db import db
from utils.event import get_event_class


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


  @classmethod
  @abstractmethod
  def get_tx_collections(cls) -> list[str]:
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
    Returns the event model used to validate event data.
    Each subclass must define an InfoModel class that inherits from EventInfoModel.
    """
    return cls.InfoModel

  @classmethod
  def create_as_child(cls, context: EventInfoModel, new_event_data: 'cls.InfoModel') -> Self:
    """
    Create a child event from an existing event, passing event group id, transaction, and user/session data.
    """
    info = context.info.model_dump()
    info['primary'] = False
    info.update(dict(**new_event_data, event_type = cls.get_event_type()))
    new_event = cls(tx = context.tx, info = info)
    new_event.save()
    return new_event.response


  @staticmethod
  def spawn_multiple(
    shared_data: EventInfoModel,
    event_data: list[dict],
    tx: TransactionDatabase | None = None,
    ) -> None:
    """
    Generate multiple events from a list of event data sharing the same transaction and group id
    without the need to have a single primary event.
    """

    if not event_data:
      return

    # All events must share the same event group
    if shared_data.event_group is None:
      shared_data.event_group = str(uuid.uuid4())

    # If no transaction is provided, create one with the collections of all event types
    commit = False
    if tx is None:
      commit = True
      try:
        event_classes = [get_event_class(data.get('event_type')) for data in event_data]
        collections = set(sum((event_class.get_tx_collections() for event_class in event_classes), []))
      except KeyError:
        raise ValueError('Event type is required')

      tx = db.begin_transaction(write=collections)

    # Create and process each event
    for data in event_data:
      try:
        event_type = data.get('event_type')
      except KeyError:
        raise ValueError('Event type is required')

      try:
        event_class = get_event_class(event_type)
      except KeyError:
        raise ValueError(f'Invalid event type: {event_type}')

      context = EventModel(tx=tx, info=shared_data)
      event = event_class.create_as_child(context=context, new_event_data=data)
      event.save()

    if commit:
      tx.commit_transaction()

  @property
  def event_first(self) -> bool:
    """
    Can be overridden by subclasses to determine if the event must be stored in the database before being processed.
    """
    # TODO: Consider always storing events in the database first, and then processing them to remove the need for this property and dual logic
    return False

  # ================================
  # INITIALIZATION METHOD
  # ================================
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

  # ================================
  # PRE/POST PROCESSING METHODS
  # ================================
  def pre_processing(self):
    """
    Can be overridden by subclasses to perform any pre-processing steps.
    """
    pass

  def post_processing(self):
    """
    Can be overridden by subclasses to perform any post-processing steps.
    """
    pass

  # ================================
  # STORE EVENT METHOD
  # ================================
  def store_event(self):
    """
    Store the event in the database.
    """
    record = self.info.model_dump(exclude_extra=True)
    # update with data modified through the apply method
    if hasattr(self, 'event_key'):
      record.update(dict(_key=self.event_key))

    self.event_key = self.tx.collection('Event').insert(record, overwrite=True)['_key']

  # ================================
  # SAVE EVENT METHOD
  # ================================
  def save(self):
    """
    Save the event to the database and handle transaction.
    """
    collections = self.get_tx_collections() + ['Event']

    try:
      if self.info.primary:
        self.tx = db.begin_transaction(write=collections)
        self.info.event_group = str(uuid.uuid4())

      if self.event_first:
        self.store_event()

      # Perform any pre-processing steps
      self.pre_processing()

      # Apply updates to global application state based on specific event
      self.apply()

      # Perform any post-processing steps
      self.post_processing()

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
