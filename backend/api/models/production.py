from datetime import date, datetime, timedelta
from dateutil import tz
from enum import Enum
from typing import Dict, List, Union

from pydantic import Field, validator

from models.bom import BomLineRead
from models.process import PhaseParameters, StepWithMediaInfo
from models.product import ProductDoc
from utils.base_models import FlexModel, ArangoDocument



class CustomerData(FlexModel):
  customer_key: str = None
  customer_name: str = None
  delivery_address: str = None
  order_code: str = None
  order_line: int = None
  po_code: str = None

class TimeDeltaInfo(FlexModel):
  absolute: timedelta = None
  relative: float = None

  # @validator('relative')
  # def above_minus_100percent(cls, v):
  #   if v <= -1:
  #     raise ValueError("Relative time delta must be above -100%")
  #   return v

class TargetActualTimeDelta(FlexModel):
  target: timedelta = None
  actual: timedelta = None
  delta: TimeDeltaInfo = TimeDeltaInfo()

# class TargetActualTime(FlexModel):
#   target: datetime = None
#   actual: datetime = None
#   delta: timedelta = None


class WorkStatus(Enum):
  CREATED = 'created'
  PLANNED = 'planned'
  STARTED = 'started'
  CLOSED = 'closed'


class WorkOrderNew(ArangoDocument):
  customer_data: CustomerData = CustomerData()
  wo_code: str
  wo_line: int = 1
  product_key: str
  product_code: str = None
  product_description: str = None
  phase_sequence: List[str] = []
  qt_planned: float
  # priority: bool = False
  due_by: Union[datetime, date] = None


class WorkOrderFull(WorkOrderNew):
  key: str = Field(None, alias="_key")

  status: WorkStatus = WorkStatus.CREATED
  qt_completed: float = 0
  active: bool = False
  on_time: bool = True
  critical: bool = False
  progress: int = Field(0, ge=0, le=100)

  created: datetime = datetime.now(tz.UTC)
  start: datetime = None
  end: datetime = None

  lead_time: float = None # TargetActualTimeDelta = TargetActualTimeDelta()
  throughput_time: float = None # TargetActualTimeDelta = TargetActualTimeDelta()
  processing_time: float = None # TargetActualTimeDelta = TargetActualTimeDelta()

  processing_cost: float = None
  material_cost: float = None
  total_cost: float = None

  phase_sequence: List[str] = []
  wo_docs: List[ProductDoc] = []
  wo_bom: List[BomLineRead] = []

  notes: str = None


class RequiredAvailableQt(FlexModel):
  required: float = None
  available: float = None
  stockout: bool = None


class Operator(FlexModel):
  key: str = Field(..., alias="_key")
  name: str
  surname: str
  active: bool = None
  department_key: str = None


class Job(FlexModel):
  key: str = Field(None, alias="_key")
  wo_key: str
  wo_code: str
  wo_line: int
  phase_key: str
  phase_alias: str
  product_key: str
  product_code: str
  product_description: str
  # operation_key: str >>> TODO: Fix Phase API to add op_id during creation

  parameters: PhaseParameters = None

  first_phase: bool = None
  input_available: bool = None # WIP ONLY: This does not consider Production Items and subassemblies from other work orders

  stage: WorkStatus = WorkStatus.CREATED
  active: bool = False
  critical: bool = False
  start: datetime = None
  end: datetime = None

  qt_planned: float
  qt_completed: float = 0
  qt_released: float = 0
  step_sequence: List[StepWithMediaInfo] = []

  assigned_to: Union[str, Operator] = None

  progress: int = Field(0, ge=0, le=100)
  current_batch: str = None # batch _key
  # current_step: int = None

  on_time: bool = True
  estimated_remaining_time: timedelta = None
  estimated_completion: datetime = None

  last_work_session_started: str = None
  last_online: datetime = None

  job_docs: List[ProductDoc] = []
  job_bom: List[BomLineRead] = []


  # @validator('progress')
  # def between_0_and_100_percent(cls, v):
  #   if v < 0 or v > 1:
  #     raise ValueError("Progress must be between 0 and 100%")
  #   return v

  @validator('qt_released')
  def released_less_than_completed(cls, qt_released, values):
    if qt_released > values['qt_completed']:
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
#   jobs: List[Job]

class JobUpdateType(Enum):
  INSERT = 'insert'
  UPDATE = 'update'
  DELETE = 'delete'
  REORDER = 'reorder'

class JobUpdate(FlexModel):
  action: JobUpdateType
  data: dict

  # @validator('action')
  # def check_key_or_id(cls, action, values):
  #   # If action is delete or update, data must contain _id or _key field
  #   id_key = ['_id', '_key']
  #   print(cls, action, values)
  #   if action != JobUpdateType.INSERT and any([k in values['data'] for k in id_key]):
  #     raise ValueError("Job Update and Delete operations require Job key")
  #   return action




class WorkOrderDetails(WorkOrderFull):
  jobs: List[Job]


class OperatorAssignments(FlexModel):
  operator: Operator
  assigned_jobs: List[Job] = None


class AssignmentsResponse(FlexModel):
  assigned_jobs_by_operator: List[OperatorAssignments] = []
  unassigned_jobs: List[Job] = []


class QueueType(Enum):
  OPERATOR = 'o'
  EQUIPMENT = 'e'
  SITE = 's'


class Queue(ArangoDocument):
  type: QueueType #What the queue refers to.
  site_key: str = None
  subqueue_target_key: str = None # id of operator / equipment
  work_orders: List[str] = None # the list of Wo keys ordered by priority.
  jobs: List[str] = None # the list of job keys ordered by priority
