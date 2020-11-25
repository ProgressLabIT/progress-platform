from datetime import datetime, timedelta
from enum import Enum
from typing import Any, List

from pydantic import Field

from models.process import StepWithMediaInfo
from utils.base_models import FlexModel, ArangoDocument, ArangoEdge



class StepStatus(Enum):
  TODO = 'to_do'
  DONE = 'done'
  CRITICAL = 'critical'


class StepExecutionData(FlexModel):
  key: str = Field(None, alias="_key")
  job_key: str = None
  user_key: str = None
  work_session_key: str = None
  batch_key: str = None
  step_key: str = None
  # start: datetime = None
  completed: datetime = None
  # duration: timedelta = None
  status: StepStatus = StepStatus.TODO
  user_data: list = None


class Batch(FlexModel):
  key: str = Field(None, alias="_key")
  job_key: str

  start: datetime
  end: datetime = None
  # duration: timedelta = None
  active: bool = True
  # serial_numbers: List[str] = None

  qt_pass: float = 0
  qt_scrap: float = 0

  unit_processing_time: float = 0
  unit_processing_cost: float = 0
  unit_material_cost: float = 0
  value: float = 0

  # next_step: int = None
  step_data: List[StepExecutionData] = None
  


class WorkSession(FlexModel):
  key: str = Field(None, alias="_key")
  user_session_key: str
  job_key: str
  user_key: str
  # master_session: bool
  start: datetime = None
  end: datetime = None
  # duration: timedelta = None
  active: bool
  hourly_cost: float = None


class EventType(Enum):
  JOB_STARTED = 'JOB_STARTED'
  JOB_PAUSED = 'JOB_PAUSED'
  JOB_RESUMED = 'JOB_RESUMED'
  JOB_CLOSED = 'JOB_CLOSED'
  STEP_COMPLETED = 'STEP_COMPLETED'
  BATCH_COMPLETED = 'BATCH_COMPLETED'


class ProductionEvent(FlexModel):
  key: str = Field(None, alias="_key")
  event_type: EventType
  user_key: str
  user_session_key: str
  work_session_key: str = None
  job_key: str = None
  product_key: str = None
  work_order_key: str = None
  phase_key: str = None
  next_phase: str = None
  current_batch_key: str = None
  step_key: str = None
  completed_batch_key: str = None
  completed_batch_qt: float = None
  new_batch_key: str = None
  timestamp: datetime
  user_data: Any


class BatchTimeRecord(FlexModel):
  key: str = Field(None, alias="_key")
  batch_key: str
  work_session_key: str
  full_session: bool = None
  start: datetime
  end: datetime = None
  duration: float = None
  value: float = None
  active: bool = None
  product_key: str = None
  work_order_key: str = None
  phase_key: str = None




# class Serial(ArangoDocument):
#   wo_key: str
#   counter: int
#   product_key: str
#   start: datetime = None
#   end: datetime = None
#   accept: bool = True
#   batches: List[str]
#   value: float = None


class WIP(ArangoEdge):
  batch_key: str
  wo_key: str
  product_key: str
  value: float = 0
  quantity: float = 0
  # serial_numbers: List[str] = None

