from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from models.base_models import FlexModel, ArangoEdge, ArangoDocument
from models.form import SerialFormFieldValue
from utils.dt import timestamp

class Serial(ArangoDocument):
   code: str | None = None
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

class SerialCommandType(str, Enum):
  CREATE_FROM_BATCH = 'CREATE_FROM_BATCH'
  UPDATE_DATA_FROM_BATCH = 'UPDATE_DATA_FROM_BATCH'
  FINALIZE_BATCH = 'FINALIZE_BATCH'
  FINALIZE_WO = 'FINALIZE_WO'
  CREATE_AND_FINALIZE = 'CREATE_AND_FINALIZE'
  UPDATE = 'UPDATE'
  DELETE = 'DELETE'
  LINK_BATCH = 'LINK_BATCH'
  LINK_SERIALS = 'LINK_SERIALS'

class SerialSelection(BaseModel):
   serial_key: str | None = Field(None, validation_alias='_key')
   serial_code: str | None = Field(None, validation_alias='code')
   active: bool = False

class SerialLink(BaseModel):
  from_serial: str
  to_serial:str
  wo_key: str | None = None,
  component_key: str | None = None,
  batch_key: str | None = None,
  replaced: bool = False
  reason: str | None = None
  link_serial_directly: bool = False

class SerialEvent(Serial):
   operation: SerialCommandType | None = None
   batch_key: str | None = None
   serial: Serial | None = None
   serial_key: str | None = None
   step_data: list[SerialFormFieldValue] | None = None
   created_by: str | None = None
   quantity: int | float | None = 1
   wo_key: str | None = None
   product_key: str | None = None
   batch_serials: list[SerialSelection] | list[str] | None = None
   serial_link_data: list[SerialLink] | None = None
   last_phase: bool = False
   traceability_level: str | None = None

class SerialNotificationType(str, Enum):
  CREATED = 'CREATED'
  UPDATED = 'UPDATED'
  DELETED = 'DELETED'
  FINALIZED = 'FINALIZED'
  ERROR = 'ERROR'

class SerialNotificationErrorCode(str, Enum):
  SERIAL_ALREADY_PRESENT = 'SERIAL_ALREADY_PRESENT'
  COUNTER_NOT_DEFINED = 'COUNTER_NOT_DEFINED'
  EXCEPTION = 'EXCEPTION'


class SerialNotification(BaseModel):
   serial: str | None = None
   serial_key: str | None = None
   notification: SerialNotificationType | None = None
   error_code: SerialNotificationErrorCode | None = None
   error: str | None = None

