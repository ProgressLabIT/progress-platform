from datetime import datetime
from enum import Enum
from typing import Annotated

from models.base_models import ArangoDocument, FlexModel
from models.form import SerialFormFieldValue
from pydantic import BaseModel, Field, StringConstraints, field_serializer, field_validator, BeforeValidator
from utils.dt import timestamp


def process_serial_code(code: str | None) -> str | None:
  if code is None:
    return None
  if not isinstance(code, str):
    raise ValueError('Serial code must be a string')
  code = code.upper().strip()

  return code


ProcessedSerialCode = Annotated[str | None, BeforeValidator(process_serial_code)]


class Serial(ArangoDocument):
  code: Annotated[str, StringConstraints(to_upper=True, strip_whitespace=True, min_length=1)] | None = Field(None, description="Serial number code, normalized to uppercase. Unique within a product scope.", examples=["SN-LR-001234"])
  created_by: str | None = Field(None, description="User key of the operator who created the serial.", examples=["user/operator-01"])
  product_key: str | None = Field(None, description="Key of the product this serial belongs to.", examples=["67890"])
  wo_key: str | None = Field(None, description="Key of the work order under which this serial was created.", examples=["WO-2026-001"])
  counter_key: str | None = Field(None, description="Key of the counter used to auto-generate this serial's code.", examples=["counter/sn-lr"])
  user_key: str | None = Field(None, description="Key of the user associated with this serial at creation time.", examples=["user/operator-01"])
  quantity: int = Field(1, description="Quantity represented by this serial record (typically 1 for unit-tracked serials).", examples=[1])
  created: datetime | None = Field(default_factory=timestamp, description="Timestamp when the serial was created.", examples=["2026-05-15T10:00:00Z"])
  released: datetime | None = Field(None, description="Timestamp when the serial was released to inventory. None if still in WIP.", examples=["2026-05-16T08:00:00Z"])
  data: list[SerialFormFieldValue] | None = Field([], description="Custom field values recorded against this serial (e.g. test results, supplier batch).", examples=[[]])
  deleted: str | bool | None = Field(False, description="False if not deleted; the event key string if logically deleted via a serial deletion event.", examples=[False])

class SerialSelection(BaseModel):
   serial_key: str | None = Field(None, validation_alias='_key', description="ArangoDB document key of the serial.", examples=["SN-LR-001234"])
   serial_code: str | None = Field(None, validation_alias='code', description="Human-readable serial code.", examples=["SN-LR-001234"])
   counter_key: str | None = Field(None, validation_alias='counter_key', description="Counter key used to generate this serial's code.", examples=["counter/sn-lr"])
   active: bool = Field(False, description="True when the serial is currently assigned to an active batch.", examples=[False])

class SerialLink(FlexModel):
  parent_serial_key: str = Field(..., alias='_from', description="Key of the parent serial in the `contains` edge. Use `components` or `None` to link directly to a batch.", examples=["SN-LR-001234"])
  child_serial_key: str = Field(..., alias='_to', description="Key of the child (component) serial.", examples=["SN-LR-005678"])
  key: str | None = Field(None, alias='_key', description="ArangoDB document key of the `contains` edge.", examples=["link-001"])
  wo_key: str | None = Field(None, description="Work order key associated with this link.", examples=["WO-2026-001"])
  phase_key: str | None = Field(None, description="Phase key associated with this link.", examples=["phase/ph-01"])
  component_key: str | None = Field(None, description="BOM component key that this link satisfies.", examples=["comp/bom-01"])
  job_key: str | None = Field(None, description="Job key associated with this link.", examples=["job/job-2026-001"])
  batch_key: str | None = Field(None, description="Batch key associated with this link.", examples=["BATCH-A-042"])
  confirmed: bool | None = Field(False, description="True if this link was confirmed via `SerialLinkedEvent`; False for temporary links.", examples=[False])
  replaced: bool | None = Field(False, description="True if this link has been superseded by a replacement.", examples=[False])
  reason: str | None = Field(None, description="Free-text reason for creating or replacing this link.", examples=["Component replaced due to defect"])

  @field_serializer('parent_serial_key', 'child_serial_key')
  def generate_serial_id(self, serial_key, _info):
    return f'Serial/{serial_key}' if '/' not in serial_key else serial_key

  @field_validator('parent_serial_key', 'child_serial_key', mode="after")
  @classmethod
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
   serial: str | None = Field(None, description="Serial code that triggered the notification.", examples=["SN-LR-001234"])
   serial_key: str | None = Field(None, description="ArangoDB key of the serial.", examples=["SN-LR-001234"])
   notification: SerialNotificationType | None = Field(None, description="Type of notification event.", examples=["CREATED"])
   error_code: SerialNotificationErrorCode | None = Field(None, description="Error code if `notification=ERROR`.", examples=[None])
   error: str | None = Field(None, description="Error detail message if `notification=ERROR`.", examples=[None])


class SerialTreeNode(BaseModel):
  serial_key: str | None = Field(None, description="Key of this serial in the `Serial` collection.", examples=["SN-LR-001234"])
  product_key: str | None = Field(None, description="Key of the product this serial represents.", examples=["67890"])
  serial_code: str | None = Field(None, description="Human-readable serial code.", examples=["SN-LR-001234"])
  product_code: str | None = Field(None, description="Code of the product.", examples=["PROD-001"])
  replaced: bool | None = Field(False, description="True if this serial has been replaced by another in its parent's BOM.", examples=[False])
  confirmed: bool | None = Field(True, description="True if the link from parent to this serial is confirmed.", examples=[True])
  extra_bom: bool | None = Field(False, description="True if this serial is an extra BOM component not in the original BOM.", examples=[False])
  product_description: str | None = Field(None, description="Description of the product.", examples=["Steel bracket M6"])
  children: list["SerialTreeNode"] = Field([], description="Recursive list of child serial nodes.", examples=[[]])
