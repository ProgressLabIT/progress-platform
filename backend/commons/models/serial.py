from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from commons.models.base_models import FlexModel, ArangoEdge, ArangoDocument
from commons.models.form import SerialFormFieldValue

class Serial(ArangoDocument):
   serial: str | None = None
   created_by: str | None = None
   product_key: str | None = None
   wo_key: str | None = None
   counter_key: str | None = None
   user_key: str | None = None
   quantity: int = 1
   created: datetime | None = None
   released: datetime | None = None
   data: list[SerialFormFieldValue] | None = None
   deleted: bool = False

class SerialEventType(str, Enum):
  CREATE = 'CREATE'
  UPDATE = 'UPDATE'
  DELETE = 'DELETE'
  UPDATE_DATA = 'UPDATE_DATA'
class SerialEvent(Serial):
   operation: SerialEventType | None = None
   batch_key: str | None = None
   serial: Serial | None = None
   serial_key: str | None = None
   step_data: list[SerialFormFieldValue] | None = None

class SerialNotificationType(str, Enum):
  CREATED = 'CREATED'
  UPDATED = 'UPDATED'
  DELETED = 'DELETED'
  ERROR = 'ERROR'
class SerialNotification(BaseModel):
   serial: str | None = None
   serial_key: str | None = None
   notification: SerialNotificationType | None = None
   error: str | None = None

