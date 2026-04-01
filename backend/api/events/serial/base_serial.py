import json
import logging
from abc import ABC
from typing import Any

from events.base_event import BaseEvent
from models.event import EventInfoModel
from models.serial import Serial, SerialNotificationType
from utils.nats_client import publish_sync, subtopic_to_subject
from utils.serial import Queries

logger = logging.getLogger("base_serial")


class BaseSerialModel(EventInfoModel):
   # Traceability fields
   serial_key: str | None = None
   code: str | None = None
   product_key: str | None = None


class BaseSerialEvent(BaseEvent, ABC):
  _notification_subtopic = "serial"

  @classmethod
  def get_tx_collections(cls):
    return [
      'Batch',
      'batch_serial',
      'Event',
      'Job',
      'Queue',
      'Serial',
      'StepExecutionData',
      'wip',
      'WorkOrder',
      'WorkSession',
      'contains',
      'Config',
      'Counter'
    ]

  def notify_error(self, notification):
    """Send an immediate error notification via NATS (bypasses auto-publish since tx will abort)."""
    notification['subtopic'] = "serial"
    try:
      subject = subtopic_to_subject("serial")
      publish_sync(subject, json.dumps(notification, default=str))
    except Exception:
      logger.exception("Failed to publish serial error notification")

  def verify_serial_code_free(self, serial_key, product_key, serial):
     cursor = self.tx.aql.execute(
        Queries.GET_SERIALS_FOR_SERIAL_CODE,
        bind_vars=dict(
          serial_key=serial_key,
          serial=serial,
          product_key=product_key
        )
      )
     try:
        return len([Serial(**t) for t in cursor])<=0
     except:
      return False
