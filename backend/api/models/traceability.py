from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from models.form import FormFieldValue
from models.base_models import FlexModel, ArangoEdge, ArangoDocument


class StepStatus(str, Enum):
  TODO = 'to_do'
  DONE = 'done'
  CRITICAL = 'critical'


class StepExecutionData(FlexModel):
  key: str | None = Field(None, alias="_key", description="ArangoDB document key of the step execution record.", examples=["exec-record-001"])
  job_key: str | None = Field(None, description="Key of the job this execution data belongs to.", examples=["job/job-2026-001"])
  user_key: str | None = Field(None, description="Key of the user who completed the step.", examples=["user/operator-01"])
  work_session_key: str | None = Field(None, description="Key of the work session during which the step was completed.", examples=["ws-001"])
  batch_key: str | None = Field(None, description="Key of the production batch this step execution belongs to.", examples=["BATCH-A-042"])
  step_key: str | None = Field(None, description="Key of the process step definition being executed.", examples=["step/quality-check-01"])
  # start: datetime | None = None
  completed: datetime | None = Field(None, description="Timestamp when the step was marked as done.", examples=["2026-05-15T11:30:00Z"])
  # duration: timedelta | None = None
  status: StepStatus = Field(StepStatus.TODO, description="Current execution status of the step.", examples=["to_do"])
  form_data: list[FormFieldValue] = Field([], description="List of form field values recorded for this step.", examples=[[]])

  modified: str | None = Field(None, description="Event key of the last `STEP_EDITED` event that modified this record.", examples=[None])
  canceled: str | None = Field(None, description="Event key of the event that canceled this execution record.", examples=[None])


class ExecutionDataUpdate(BaseModel):
  step_key: str | None = Field(None, description="Key of the step to update. Required when `execution_record_key` is not provided.", examples=["step/quality-check-01"])
  batch_key: str | None = Field(None, description="Key of the batch. Required when `execution_record_key` is not provided.", examples=["BATCH-A-042"])
  execution_record_key: str | None = Field(None, description="Key of an existing `StepExecutionData` record to update directly.", examples=["exec-record-001"])
  form_data: list[FormFieldValue] = Field([], description="Form field values to merge into the existing or new execution record.", examples=[[]])


class Batch(FlexModel):
  key: str | None = Field(None, alias="_key", description="ArangoDB document key of the batch.", examples=["BATCH-A-042"])
  job_key: str = Field(..., description="Key of the job that owns this batch.", examples=["job/job-2026-001"])
  phase_key: str = Field(..., description="Key of the process phase this batch executes.", examples=["phase/ph-01"])
  work_order_key: str = Field(..., description="Key of the work order this batch belongs to.", examples=["WO-2026-001"])
  product_key: str | None = Field(None, description="Key of the product being produced in this batch.", examples=["67890"])

  start: datetime = Field(..., description="Timestamp when the batch was started.", examples=["2026-05-15T09:00:00Z"])
  end: datetime | None = Field(None, description="Timestamp when the batch was completed or closed.", examples=["2026-05-15T11:00:00Z"])
  # duration: timedelta | None = None
  active: bool = Field(True, description="True while the batch is currently in progress.", examples=[True])
  # serial_numbers: List[str] = []

  qt_pass: float = Field(0, description="Quantity that passed quality checks in this batch.", examples=[10.0])
  qt_scrap: float = Field(0, description="Quantity scrapped in this batch.", examples=[0.0])
  qt_total: float = Field(0, description="Total quantity processed in this batch.", examples=[10.0])

  unit_material_cost: float = Field(0, description="Material cost per unit produced in this batch.", examples=[12.5])
  value: float = Field(0, description="Total material value of the batch output.", examples=[125.0])

  # next_step: int | None = None
  step_data: list[StepExecutionData] | None = Field(None, description="List of step execution data records linked to this batch.", examples=[None])

  # Attributes for overrides
  canceled: str | None = Field(None, description="Event key of the event that canceled this batch.", examples=[None])
  forced: str | None = Field(None, description="Event key of the event that forced-closed this batch.", examples=[None])


class WorkSession(FlexModel):
  key: str | None = Field(None, alias="_key", description="ArangoDB document key of the work session.", examples=["ws-001"])
  user_session_key: str | None = Field(None, description="Key of the user's login session.", examples=["usession-001"])
  batch_key: str = Field(..., description="Key of the batch this work session is associated with.", examples=["BATCH-A-042"])
  job_key: str = Field(..., description="Key of the job.", examples=["job/job-2026-001"])
  phase_key: str = Field(..., description="Key of the process phase.", examples=["phase/ph-01"])
  work_order_key: str = Field(..., description="Key of the work order.", examples=["WO-2026-001"])
  product_key: str = Field(..., description="Key of the product being produced.", examples=["67890"])
  user_key: str | None = Field(None, description="Key of the operator.", examples=["user/operator-01"])
  # master_session: bool
  start: datetime | None = Field(None, description="Timestamp when the operator started this work session.", examples=["2026-05-15T09:00:00Z"])
  end: datetime | None = Field(None, description="Timestamp when the operator ended this work session.", examples=["2026-05-15T11:00:00Z"])
  duration: int | None = Field(None, description="Duration of the work session in milliseconds.", examples=[7200000])
  active: bool = Field(False, description="True while the operator is actively in this work session.", examples=[True])
  hourly_cost: float | None = Field(None, description="Operator hourly cost rate at the time of the session.", examples=[35.0])

  # Attributes for overrides
  canceled: str | None = Field(None, description="Event key of the event that canceled this work session.", examples=[None])
  forced: str | None = Field(None, description="Event key of the event that forced this work session closed.", examples=[None])

  @field_validator('duration', mode="before")
  @classmethod
  def truncate_duration(cls, v) -> int:
    return int(v) if type(v) == float else v

class WIP(ArangoEdge):
  # _from & _to refer to process phases or specific jobs
  wo_key: str = Field(..., description="Key of the work order this WIP belongs to.", examples=["WO-2026-001"])
  product_key: str = Field(..., description="Key of the product represented by this WIP.", examples=["67890"])
  serial_key: str | None = Field(None, description="Key of the serial number if this WIP is unit-tracked.", examples=["SN-LR-001234"])
  value: float = Field(0, description="Monetary value of this WIP record.", examples=[125.0])
  quantity: float = Field(0, description="Quantity of product in WIP.", examples=[5.0])
  active: bool = Field(False, description="True while this WIP is currently being worked on.", examples=[False])
