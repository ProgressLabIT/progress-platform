import uuid
from abc import ABC, abstractmethod
from typing import Self

from arango.database import TransactionDatabase
from models.event import EventInfoModel, EventModel, EventType
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
  def create_as_child(cls, parent_event: EventModel, new_event_data: 'cls.InfoModel') -> Self:
    """
    Create a child event from an existing event, passing event group id, transaction, and user/session data.
    """
    info = parent_event.info.model_dump()
    info['primary'] = False
    info.update(dict(**new_event_data, event_type = cls.get_event_type()))

    # Create child event (gets UUID key immediately in __init__)
    new_event = cls(tx = parent_event.tx, info = info)

    # Create edge immediately since both events have keys
    new_event.store_event_source(parent_event.event_key)

    new_event.save()
    return new_event.response


  @staticmethod
  def spawn_multiple(
    shared_data: EventInfoModel,
    event_data: list[dict],
    tx: TransactionDatabase | None = None,
    ) -> list:
    """
    Generate multiple events from a list of event data sharing the same transaction and group id.
    All events must be of the same type (specified in shared_data.event_type).
    """

    if not event_data:
      return []

    if tx is None:
      # If spawn multiple is used without a transaction, it means that events are triggered by the user, so they are primary.
      _primary_events = True

    # All events must share the same event group
    if shared_data.event_group is None:
      shared_data.event_group = str(uuid.uuid4())

    # Get event type from shared data (all events are of the same type)
    try:
      event_type = shared_data.event_type
      event_class = get_event_class(event_type)
    except (AttributeError, KeyError):
      raise ValueError('Event type is required in shared_data')

    # If no transaction is provided, create one with the collections for this event type
    commit = False
    if tx is None:
      commit = True
      collections = set(event_class.get_tx_collections())
      collections.add('Event')  # Ensure Event collection is included
      tx = db.begin_transaction(write=collections)

    # Create and process each event
    created_events = []
    for data in event_data:
      # Build child event info using shared_data and override with specific event data
      info_data = shared_data.model_dump()
      info_data['primary'] = _primary_events
      info_data.update(data)

      event = event_class(info=info_data, tx=tx)
      event.save()
      created_events.append(event)

    if commit:
      tx.commit_transaction()


  # ================================
  # INITIALIZATION METHOD
  # ================================
  def __init__(self, info, tx: TransactionDatabase | None = None):
    self.tx = tx
    self._owns_transaction = (tx is None)
    self.response = None

    # Generate UUID for event key immediately
    self.event_key = str(uuid.uuid4())

    # Validate general event properties
    # Secondary events must have both transaction and event_group
    if not info['primary']:
      if tx is None or info['event_group'] is None:
        raise ValueError('Secondary events must be initialized with a transaction and event_group')

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
  # STORE EVENT DATA
  # ================================
  def store_event(self):
    """
    Store the event in the database using the pre-generated UUID key.
    """
    record = self.info.model_dump(exclude_extra=True, by_alias=True)
    record['_key'] = self.event_key  # Use pre-generated UUID

    # Insert with specific key (no overwrite needed since key is unique)
    self.tx.collection('Event').insert(record)

  def store_event_source(self, parent_event_key: str):
    """
    Store the event source relationship in the database.
    Creates an edge from parent event to this child event.
    """
    self.tx.collection('event_source').insert(dict(
      _from=f'Event/{parent_event_key}',
      _to=f'Event/{self.event_key}'
    ))

  # ================================
  # SAVE EVENT METHOD
  # ================================
  def save(self):
    """
    Save the event to the database and handle transaction.
    """
    collections = self.get_tx_collections() + ['Event', 'event_source']

    try:
      # Create transaction if this event owns it
      if self._owns_transaction:
        self.tx = db.begin_transaction(write=collections)

      # Initialize event group for primary events if not already set
      if self.info.primary and self.info.event_group is None:
        self.info.event_group = str(uuid.uuid4())

      # Perform any pre-processing steps
      self.pre_processing()

      # Apply updates to global application state based on specific event
      self.apply()

      # Perform any post-processing steps
      self.post_processing()

      # Store event with all final data
      self.store_event()

      # Commit transaction only if this event owns it
      if self._owns_transaction:
        self.tx.commit_transaction()

      # Return any required value
      return self.response

    # In case of exceptions abort transaction without catching them if transaction is still open
    finally:
      if self._owns_transaction and self.tx.transaction_status() == 'running': # See transaction statuses in the HTTP API of ArangoDB
        self.tx.abort_transaction()
