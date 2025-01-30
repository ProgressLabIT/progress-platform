from abc import ABC, abstractmethod
from typing import Any
import uuid
from pydantic import model_validator, Field
from events.event_type import EventType
from events.event_model import EventModel
from utils.dt import timestamp
from datetime import datetime
from utils.db import db

class BaseEvent(ABC):
  """fields marked with a comment are event attributes, the rest could be refactored into a generic "data" field, which can be defined with additional models specific for the event type."""
  event_data: Any
  event_type: EventType

  response: dict | None = dict()
  child_responses: list[dict] = []

  tx: Any | None = None

  def __init__(self):
    self.tx = None
    self.response = dict()
    self.child_responses: list[dict] = []

  @abstractmethod
  def apply(self):
    pass

  @abstractmethod
  def set_model(self, base_model: EventModel):
    pass

  def validate_event(self):
    return True

  def get_write_collections(self):
    return []

  def set_transaction(self, tx):
    self.tx = tx
#
#
  def not_handled_response(self, reason):
    self.response = dict(
      notification = 'Not handled',
      reason = reason
    )

  def post_processing(self):
    pass

  def is_event_first(self):
    return False

  def notify_results(self, notification):
    pass

  def set_response(self, response):
      self.response = response

  def get_response(self):
      return self.response
