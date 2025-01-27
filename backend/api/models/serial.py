from datetime import datetime
from typing import Annotated
from enum import Enum
from pydantic import BaseModel, Field, field_validator, StringConstraints
from models.base_models import FlexModel, ArangoEdge, ArangoDocument
from models.form import SerialFormFieldValue
from utils.dt import timestamp

class Serial(ArangoDocument):
  code: Annotated[str, StringConstraints(to_upper=True)] | None = None
  created_by: str | None = None
  product_key: str | None = None
  wo_key: str | None = None
  counter_key: str | None = None
  user_key: str | None = None
  quantity: int = 1
  created: datetime | datetime = Field(default_factory=timestamp)
  released: datetime | None = None
  available: bool = True
  data: list[SerialFormFieldValue] | None = None
  deleted: bool = False

class SerialSelection(BaseModel):
   serial_key: str | None = Field(None, validation_alias='_key')
   serial_code: str | None = Field(None, validation_alias='code')
   counter_key: str | None = Field(None, validation_alias='counter_key')
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

class SerialNotificationType(str, Enum):
  CREATED = 'CREATED'
  UPDATED = 'UPDATED'
  DELETED = 'DELETED'
  FINALIZED = 'FINALIZED'
  ERROR = 'ERROR'

class SerialNotificationErrorCode(str, Enum):
  SERIAL_ALREADY_PRESENT = 'SERIAL_ALREADY_PRESENT'
  COUNTER_NOT_DEFINED = 'COUNTER_NOT_DEFINED'
  SERIAL_CODE_EDIT_NOT_ALLOWED = 'SERIAL_CODE_EDIT_NOT_ALLOWED'
  EXCEPTION = 'EXCEPTION'


class SerialNotification(BaseModel):
   serial: str | None = None
   serial_key: str | None = None
   notification: SerialNotificationType | None = None
   error_code: SerialNotificationErrorCode | None = None
   error: str | None = None

