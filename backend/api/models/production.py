from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import model_validator, BaseModel, Field, PositiveFloat, field_validator, ValidationInfo

from models.bom import WOBomLine, WOBomLineInput
from models.process import PhaseParameters, StepWithMediaInfo
from models.product import ProductDoc
from models.product import TraceabilityLevel
from models.form import SerialFormFieldValue
from models.base_models import FlexModel, ArangoDocument
from utils.dt import timestamp


class TimeDeltaInfo(FlexModel):
  absolute: timedelta | None = Field(None, description="Absolute time delta as a duration.", examples=["PT3600S"])
  relative: float | None = Field(None, description="Relative time delta as a ratio (e.g. 0.1 = 10% over target).", examples=[0.1])

  # @validator('relative')
  # def above_minus_100percent(cls, v):
  #   if v <= -1:
  #     raise ValueError("Relative time delta must be above -100%")
  #   return v

class TargetActualTimeDelta(FlexModel):
  target: timedelta | None = Field(None, description="Target (planned) duration for the operation.", examples=["PT7200S"])
  actual: timedelta | None = Field(None, description="Actual elapsed duration for the operation.", examples=["PT7560S"])
  delta: TimeDeltaInfo = Field(default_factory=TimeDeltaInfo, description="Computed difference between actual and target durations.")

# class TargetActualTime(FlexModel):
#   target: datetime | None = None
#   actual: datetime | None = None
#   delta: timedelta | None = None


class WorkStatus(str, Enum):
  CREATED = 'created'
  PLANNED = 'planned'
  STARTED = 'started'
  CLOSED = 'closed'


class WorkOrderNew(BaseModel):
  wo_code: str | None = Field(None, description="Work order code. Auto-generated from counter if not provided.", examples=["WO-2026-001"])
  product_key: str | None = Field(None, description="ArangoDB key of the product to manufacture.", examples=["Product/12345"])
  product_code: str | None = Field(None, description="Human-readable product code. Used to look up product_key if key is absent.", examples=["PRD-GEAR-42"])
  product_description: str | None = Field(None, description="Product display description, copied from the Product record.", examples=["Planetary gear assembly 42mm"])
  phase_sequence: list[str] = Field(default_factory=list, description="Ordered list of phase keys defining the production routing.", examples=[["assembly", "qc"]])
  qt_planned: PositiveFloat = Field(..., description="Planned production quantity (must be positive).", examples=[100.0])
  priority: bool | None = Field(False, description="Whether the work order is flagged as high priority.", examples=[False])
  project_code: str | None = Field(None, description="Optional project code to group related work orders.", examples=["PROJ-2026-Q1"])
  start_from: datetime | date | None = Field(None, description="Earliest date/time the work order may begin.", examples=["2026-05-01T06:00:00Z"])
  due_by: datetime | date | None = Field(None, description="Deadline date/time for completing the work order.", examples=["2026-05-15T17:00:00Z"])
  wo_bom: list[WOBomLineInput] = Field(default_factory=list, description="Bill-of-materials lines overriding the product BOM for this work order.")
  output_position_key: str | None = Field(None, description="Inventory position key where completed output should be placed.", examples=["Position/67890"])
  traceability_level: TraceabilityLevel | None = Field(None, description="Traceability mode for the work order (e.g. serial, batch, or none).", examples=["serial"])
  serial_code_on_creation: bool | None = Field(False, description="When True, serial codes are generated at work order creation rather than at batch start.", examples=[False])
  notes: str | None = Field(None, description="Free-text notes visible to operators.", examples=["Urgent — customer delivery 2026-05-16"])
  extra: Any = Field(None, description="Arbitrary extra data stored alongside the work order.")

  @model_validator(mode="before")
  @classmethod
  def check_key_or_code_provided(cls, values):
    if not values.get('product_key') and not values.get('product_code'):
      raise ValueError('A product key or code must be provided')
    return values



class WorkOrderFull(ArangoDocument, WorkOrderNew):
  status: WorkStatus = Field(WorkStatus.CREATED, description="Current lifecycle status of the work order.", examples=["created"])
  qt_completed: float | None = Field(0, description="Total quantity completed across all jobs in this work order.", examples=[42.0])
  active: bool | None = Field(False, description="True when at least one job in this work order is actively being worked on.", examples=[False])
  on_time: bool | None = Field(True, description="False when the work order has missed its due_by deadline.", examples=[True])
  critical: bool | None = Field(False, description="True when the work order is on the critical path or has been manually flagged.", examples=[False])
  progress: int | None = Field(0, ge=0, description="Completion percentage (0–100) computed from qt_completed / qt_planned.", examples=[42])
  wo_bom: list[WOBomLine] | None = Field(None, description="Resolved BOM lines for this work order (may differ from product BOM).")
  serial_fields: list[SerialFormFieldValue] | None = Field(None, description="Serial form field values captured at work order level.")
  created: datetime = Field(default_factory=timestamp, description="Timestamp when the work order was created.", examples=["2026-05-01T08:00:00Z"])
  start: datetime | None = Field(None, description="Timestamp when the first job was started.", examples=["2026-05-02T07:30:00Z"])
  end: datetime | None = Field(None, description="Timestamp when the work order was closed.", examples=["2026-05-14T16:00:00Z"])

  material_cost: float | None = Field(None, description="Total material cost computed from BOM movements.", examples=[125.50])

  phase_sequence: list[str] = Field(default_factory=list, description="Ordered list of phase keys for this work order's routing.", examples=[["assembly", "qc"]])
  wo_docs: list[ProductDoc] = Field(default_factory=list, description="Product documents attached to this work order.")


class RequiredAvailableQt(FlexModel):
  required: float | None = Field(None, description="Required quantity of a component for this production run.", examples=[50.0])
  available: float | None = Field(None, description="Current available stock quantity at the relevant inventory position.", examples=[120.0])
  stockout: bool | None = Field(None, description="True when available stock is insufficient to cover the required quantity.", examples=[False])


class Operator(FlexModel):
  key: str = Field(..., alias="_key", description="ArangoDB document key of the operator (User) record.", examples=["usr-0042"])
  name: str | None = Field(None, description="Operator's first name.", examples=["Marco"])
  surname: str | None = Field(None, description="Operator's last name.", examples=["Rossi"])
  active: bool | None = Field(None, description="True when the operator account is active.", examples=[True])
  department_key: str | None = Field(None, description="Key of the department this operator belongs to.", examples=["dept-assembly"])


class Job(FlexModel):
  key: str | None = Field(None, alias="_key", description="ArangoDB document key of the job.", examples=["job-00123"])
  wo_key: str = Field(..., description="Key of the parent work order.", examples=["wo-2026-001"])
  wo_code: str = Field(..., description="Human-readable code of the parent work order.", examples=["WO-2026-001"])
  phase_key: str = Field(..., description="Key of the production phase this job executes.", examples=["phase-assembly"])
  phase_alias: str = Field(..., description="Display alias of the phase (e.g. 'Assembly', 'QC').", examples=["Assembly"])
  product_key: str = Field(..., description="Key of the product being manufactured.", examples=["Product/12345"])
  product_code: str = Field(..., description="Human-readable product code.", examples=["PRD-GEAR-42"])
  product_description: str = Field(..., description="Product display description.", examples=["Planetary gear assembly 42mm"])
  operation_key: str = Field(..., description="Key of the operation template governing this job.", examples=["op-default"])
  project_code: str | None = Field(None, description="Optional project code inherited from the work order.", examples=["PROJ-2026-Q1"])

  parameters: PhaseParameters | None = Field(None, description="Phase-specific parameters (cycle time, tools, etc.) for this job.")

  first_phase: bool | None = Field(None, description="True when this job is the first phase in the work order routing.", examples=[True])
  last_phase: bool | None = Field(None, description="True when this job is the last phase in the work order routing.", examples=[False])

  stage: WorkStatus = Field(WorkStatus.CREATED, description="Current lifecycle stage of the job.", examples=["created"])
  start_from: datetime | date | None = Field(None, description="Earliest date/time this job may be started.", examples=["2026-05-01T06:00:00Z"])
  due_by: datetime | date | None = Field(None, description="Deadline date/time for completing this job.", examples=["2026-05-10T17:00:00Z"])
  start: datetime | None = Field(None, description="Timestamp when the job was first started.", examples=["2026-05-02T07:30:00Z"])
  active: bool = Field(False, description="True when the job is currently being worked on.", examples=[False])
  critical: bool = Field(False, description="True when the job is on the critical path.", examples=[False])
  end: datetime | None = Field(None, description="Timestamp when the job was closed.", examples=["2026-05-09T16:45:00Z"])

  qt_planned: float = Field(..., description="Planned production quantity for this job.", examples=[100.0])
  qt_completed: float = Field(0, description="Quantity completed so far across all batches.", examples=[42.0])
  qt_released: float = Field(0, description="Quantity released to the next phase or to finished goods.", examples=[40.0])

  step_sequence: list[StepWithMediaInfo] = Field(default_factory=list, description="Ordered list of steps to execute for each batch in this job.")

  assigned_to: str | Operator | None = Field(None, description="Operator key string or resolved Operator document assigned to this job.", examples=["usr-0042"])

  issues_total: int | None = Field(None, description="Total number of issues linked to this job.", examples=[2])
  issues_open: int | None = Field(None, description="Number of open (unresolved) issues linked to this job.", examples=[1])

  progress: int = Field(0, ge=0, description="Completion percentage (0–100) computed from qt_completed / qt_planned.", examples=[42])
  active_batch_key: str | None = Field(None, description="Key of the currently active (in-progress) batch.", examples=["batch-00456"])  # batch _key
  active_batch_qt: float = Field(0, description="Quantity of the currently active batch.", examples=[10.0])
  next_batch_available: bool | None = Field(None, description="True when all WIP materials required for the next batch are available. WIP-only; does not account for production items from other work orders.", examples=[True])  # WIP ONLY: This does not consider Production Items and subassemblies from other work orders

  traceability_level: str | None = Field(None, description="Traceability mode for this job (serial, batch, or none).", examples=["serial"])
  serial_code_on_creation: bool | None = Field(False, description="When True, serial codes are generated at batch creation.", examples=[False])
  # current_step: int | None = None

  on_time: bool | None = Field(True, description="False when the job has exceeded its due_by deadline.", examples=[True])
  estimated_remaining_time: timedelta | None = Field(None, description="Estimated time remaining to complete the job, based on historical cycle times.", examples=["PT3600S"])
  estimated_completion: datetime | None = Field(None, description="Estimated completion timestamp based on remaining time.", examples=["2026-05-09T15:00:00Z"])

  last_work_session_started: str | None = Field(None, description="Key of the most recently started work session for this job.", examples=["ws-00789"])
  last_online: datetime | None = Field(None, description="Timestamp of the last recorded operator activity on this job.", examples=["2026-05-08T14:22:00Z"])

  job_docs: list[ProductDoc] | None = Field(default_factory=list, description="Documents attached to this job (e.g. drawings, instructions).")
  wo_bom: list[WOBomLine] | None = Field(default_factory=list, description="BOM lines associated with this job, inherited from the work order.")

  forced: str | None = Field(None, description="When set, indicates the job was force-closed or force-advanced; stores the reason.", examples=["operator override"])

  notes: str | None = Field(None, description="Free-text notes visible to operators for this job.", examples=["Check torque spec on step 3"])

  extra: Any = Field(None, description="Arbitrary extra data stored alongside the job.")

  # @validator('progress')
  # def between_0_and_100_percent(cls, v):
  #   if v < 0 or v > 1:
  #     raise ValueError("Progress must be between 0 and 100%")
  #   return v

  @field_validator('qt_released')
  @classmethod
  def released_less_than_completed(cls, qt_released: float, info: ValidationInfo):
    if qt_released > info.data['qt_completed']:
      raise ValueError("Released quantity cannot exceed completed quantity")
    return qt_released

  # @validator('jobs_downstream', 'jobs_upstream', each_item=True)
  # def check_job_id_root(cls, job_id):
  #   if not job_id.startswith("Job/"):
  #     raise ValueError("Job id must be fully specified and must start with 'Job/'")
  #   return job_id


# class PhaseJobs(FlexModel):
#   phase_alias: str
#   active: bool
#   jobs: list[Job]

class JobUpdateType(str, Enum):
  INSERT = 'insert'
  UPDATE = 'update'
  CLOSE = 'close'


class JobUpdate(FlexModel):
  action: JobUpdateType = Field(..., description="The operation to perform on the job: insert, update, or close.", examples=["update"])
  data: dict = Field(..., description="Payload dict for the action. Must contain '_key' for update/close; must contain 'phase_key' and 'qt_planned' for insert.")

  # @validator('action')
  # def check_key_or_id(cls, action, values):
  #   # If action is delete or update, data must contain _id or _key field
  #   id_key = ['_id', '_key']
  #   print(cls, action, values)
  #   if action != JobUpdateType.INSERT and any([k in values['data'] for k in id_key]):
  #     raise ValueError("Job Update and Delete operations require Job key")
  #   return action




class WorkOrderDetails(WorkOrderFull):
  jobs: list[Job] = Field(..., description="All Job records belonging to this work order, one per production phase.")


class OperatorAssignments(FlexModel):
  operator: Operator = Field(..., description="The operator whose job assignments are represented.")
  assigned_jobs: list[Job] | None = Field(None, description="Jobs currently assigned to this operator.")
  independent: bool = Field(False, description="True when this operator's queue ordering is independent of the main work order sequence.", examples=[False])


class AssignmentsResponse(FlexModel):
  assigned_jobs_by_operator: list[OperatorAssignments] = Field(default_factory=list, description="List of operators with their currently assigned jobs.")
  unassigned_jobs: list[Job] = Field(default_factory=list, description="Jobs with no operator assigned.")


class OperatorQueueUpdateInput(FlexModel):
  jobs: list[str] | None = Field(None, description="New ordered list of job keys for the operator's queue.", examples=[["job-00123", "job-00456"]])
  independent: bool | None = Field(None, description="When False, the operator queue will be reordered to match the global work order sequence.", examples=[False])


class QueueType(str, Enum):
  OPERATOR = 'o'
  EQUIPMENT = 'e'
  SITE = 's'


class Queue(ArangoDocument):
  type: QueueType = Field(..., description="Queue type: 'o' for operator, 'e' for equipment, 's' for site.", examples=["s"])  # What the queue refers to
  site_key: str | None = Field(None, description="Key of the site this queue belongs to.", examples=["site-main"])
  subqueue_target_key: str | None = Field(None, description="Key of the operator or equipment this queue is for (null for site queues).", examples=["usr-0042"])  # id of operator / equipment
  work_orders: list[str] = Field(default_factory=list, description="Ordered list of work order keys by priority (site queues only).", examples=[["wo-2026-001", "wo-2026-002"]])  # the list of Wo keys ordered by priority
  jobs: list[str] = Field(default_factory=list, description="Ordered list of job keys by priority (operator/equipment queues only).", examples=[["job-00123", "job-00456"]])  # the list of job keys ordered by priority
  independent: bool = Field(False, description="When True, this queue's ordering is independent of the parent site work order sequence.", examples=[False])  # if true, the queue's sequence is will be independent from the main work order sequence
