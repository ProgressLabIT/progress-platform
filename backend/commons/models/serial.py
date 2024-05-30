from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from commons.models.base_models import FlexModel, ArangoEdge, ArangoDocument
from commons.models.form import SerialFormFieldValue
from commons.utils.dt import timestamp

class Serial(ArangoDocument):
   serial: str | None = None
   created_by: str | None = None
   product_key: str | None = None
   wo_key: str | None = None
   counter_key: str | None = None
   user_key: str | None = None
   quantity: int = 1
   created: datetime | datetime = Field(default_factory=timestamp)
   released: datetime | None = None
   data: list[SerialFormFieldValue] | None = None
   deleted: bool = False

class SerialEventType(str, Enum):
  CREATE_FROM_BATCH = 'CREATE_FROM_BATCH'
  UPDATE_DATA_FROM_BATCH = 'UPDATE_DATA_FROM_BATCH'
  FINALIZE_BATCH = 'FINALIZE_BATCH'
  FINALIZE_JOB = 'FINALIZE_JOB'
  CREATE_AND_FINALIZE = 'CREATE_AND_FINALIZE'
  UPDATE = 'UPDATE'
  DELETE = 'DELETE'
  LINK_BATCH = 'LINK_BATCH'


class SerialEvent(Serial):
   operation: SerialEventType | None = None
   batch_key: str | None = None
   serial: Serial | None = None
   serial_key: str | None = None
   step_data: list[SerialFormFieldValue] | None = None
   created_by: str | None = None
   quantity: int = 1
   wo_key: str | None = None
   product_key: str | None = None
   batch_serials: list[str] | None = None


class SerialNotificationType(str, Enum):
  CREATED = 'CREATED'
  UPDATED = 'UPDATED'
  DELETED = 'DELETED'
  FINALIZED = 'FINALIZED'
  ERROR = 'ERROR'
class SerialNotification(BaseModel):
   serial: str | None = None
   serial_key: str | None = None
   notification: SerialNotificationType | None = None
   error: str | None = None

