from datetime import datetime
from enum import Enum
from typing import Annotated

from models.base_models import ArangoDocument, FlexModel
from models.form import SerialFormFieldValue
from pydantic import BaseModel, Field, StringConstraints, field_serializer, field_validator
from utils.dt import timestamp


class Serial(ArangoDocument):
  code: Annotated[str, StringConstraints(to_upper=True)] | None = None
  created_by: str | None = None
  product_key: str | None = None
  wo_key: str | None = None
  counter_key: str | None = None
  user_key: str | None = None
  quantity: int = 1
  created: datetime | None = Field(default_factory=timestamp)
  released: datetime | None = None
  data: list[SerialFormFieldValue] | None = None
  deleted: bool = False

class SerialSelection(BaseModel):
   serial_key: str | None = Field(None, validation_alias='_key')
   serial_code: str | None = Field(None, validation_alias='code')
   counter_key: str | None = Field(None, validation_alias='counter_key')
   active: bool = False

class SerialLink(FlexModel):
  parent_serial_key: str = Field(..., alias='_from')
  child_serial_key: str = Field(..., alias='_to')
  key: str | None = Field(None, alias='_key')
  wo_key: str | None = None
  phase_key: str | None = None
  component_key: str | None = None
  job_key: str | None = None
  batch_key: str | None = None
  confirmed: bool | None = False
  replaced: bool | None = False
  reason: str | None = None

  @field_serializer('parent_serial_key', 'child_serial_key')
  def generate_serial_id(self, serial_key, _info):
    return f'Serial/{serial_key}'

  @field_validator('parent_serial_key', 'child_serial_key', mode="after")
  def parse_serial_key(cls, v):
    return v.split('/')[-1]

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


class SerialTreeNode(BaseModel):
  serial_key: str | None = None
  product_key: str | None = None
  serial_code: str | None = None
  product_code: str | None = None
  replaced: bool | None = False
  confirmed: bool | None = True
  extra_bom: bool | None = False
  product_description: str | None = None
  children: list["SerialTreeNode"] = []