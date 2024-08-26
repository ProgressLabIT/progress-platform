from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from commons.models.form import FormFieldValue
from commons.models.base_models import FlexModel, ArangoEdge, ArangoDocument


class StepStatus(str, Enum):
  TODO = 'to_do'
  DONE = 'done'
  CRITICAL = 'critical'


class StepExecutionData(FlexModel):
  key: str | None = Field(None, alias="_key")
  job_key: str | None = None
  user_key: str | None = None
  work_session_key: str | None = None
  batch_key: str | None = None
  step_key: str | None = None
  # start: datetime | None = None
  completed: datetime | None = None
  # duration: timedelta | None = None
  status: StepStatus = StepStatus.TODO
  form_data: list[FormFieldValue] = []

  modified: str | None = None
  canceled: str | None = None


class Batch(FlexModel):
  key: str | None = Field(None, alias="_key")
  job_key: str
  work_order_key: str
  phase_key: str

  start: datetime
  end: datetime | None = None
  # duration: timedelta | None = None
  active: bool = True
  # serial_numbers: List[str] = []

  qt_pass: float = 0
  qt_scrap: float = 0
  qt_total: float = 0

  unit_material_cost: float = 0
  value: float = 0

  # next_step: int | None = None
  step_data: list[StepExecutionData] | None = None

  # Attributes for overrides
  canceled: str | None = None # Event id
  forced: str | None = None # Event id


class WorkSession(FlexModel):
  key: str | None = Field(None, alias="_key")
  user_session_key: str | None = None
  batch_key: str
  job_key: str
  phase_key: str
  work_order_key: str
  product_key: str
  user_key: str | None = None
  # master_session: bool
  start: datetime | None = None
  end: datetime | None = None
  duration: int | None = None # milliseconds
  active: bool = False
  hourly_cost: float | None = None

  # Attributes for overrides
  canceled: str | None = None
  forced: str | None = None

  @field_validator('duration', mode="before")
  def truncate_duration(cls, v) -> int:
    if type(v) == float:
      return int(v)

class WIP(ArangoEdge):
  # _from & _to refer to process phases or specific jobs
  batch_key: str
  wo_key: str
  product_key: str
  serial_key: str | None = None
  value: float = 0
  quantity: float = 0
  active: bool = False # indicates if it's being worked on or just sitting around

