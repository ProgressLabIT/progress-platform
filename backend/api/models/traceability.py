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
  # duration: timedesslta = None
  status: StepStatus = StepStatus.TODO
  user_data: list = None


class Batch(FlexModel):
  key: str = Field(None, alias="_key")
  job_key: str
  work_order_key: str
  phase_key: str

  start: datetime
  end: datetime = None
  # duration: timedelta = None
  active: bool = True
  # serial_numbers: List[str] = None

  qt_pass: float = 0
  qt_scrap: float = 0
  qt_total: float = 0

  unit_processing_time: float = 0
  unit_processing_cost: float = 0
  unit_material_cost: float = 0
  value: float = 0

  # next_step: int = None
  step_data: List[StepExecutionData] = None



class WorkSession(FlexModel):
  key: str = Field(None, alias="_key")
  user_session_key: str
  batch_key: str
  job_key: str
  phase_key: str
  work_order_key: str
  product_key: str
  user_key: str
  # master_session: bool
  start: datetime
  end: datetime = None
  duration: timedelta = None # milliseconds
  active: bool
  hourly_cost: float = None


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
  # _from & _to refer to process phases
  batch_key: str
  wo_key: str
  product_key: str
  value: float = 0
  quantity: float = 0
  active: bool = False # indicates if it's being worked on or just sitting around
  # serial_numbers: List[str] = None

