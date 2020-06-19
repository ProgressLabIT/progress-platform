from datetime import datetime, timedelta
from enum import Enum
from typing import Any, List

from pydantic import Field

from models.process import StepWithMediaInfo
from utils.base_models import FlexModel



class StepStatus(Enum):
  TODO = 'to_do'
  DONE = 'done'
  CRITICAL = 'critical'


class StepExecutionData(FlexModel):
  id: str = Field(None, alias="_id")
  key: str = Field(None, alias="_key")
  job_id: str = None
  user_id: str = None
  work_session_id: str = None
  batch_id: str = None
  step_id: str = None
  # start: datetime = None
  completed: datetime = None
  # duration: timedelta = None
  status: StepStatus = StepStatus.TODO
  user_data: list = None


class Batch(FlexModel):
  id: str = Field(None, alias="_id")
  key: str = Field(None, alias="_key")
  job_id: str

  start: datetime
  end: datetime = None
  # duration: timedelta = None
  active: bool = True

  qt_pass: float = None
  qt_scrap: float = None

  # next_step: int = None
  step_data: List[StepExecutionData] = None


class WorkSession(FlexModel):
  id: str = Field(None, alias="_id")
  key: str = Field(None, alias="_key")
  user_session_id: str
  job_id: str
  user_id: str
  # master_session: bool
  start: datetime = None
  end: datetime = None
  # duration: timedelta = None
  active: bool




class EventType(Enum):
  JOB_STARTED = 'JOB_STARTED'
  JOB_PAUSED = 'JOB_PAUSED'
  JOB_RESUMED = 'JOB_RESUMED'
  JOB_CLOSED = 'JOB_CLOSED'
  STEP_COMPLETED = 'STEP_COMPLETED'
  BATCH_COMPLETED = 'BATCH_COMPLETED'


class ProductionEvent(FlexModel):
  id: str = Field(None, alias="_id")
  key: str = Field(None, alias="_key")
  event_type: EventType
  user_key: str
  user_session_key: str
  job_id: str = None
  work_session_id: str = None
  phase_id: str = None
  current_batch_id: str = None
  step_id: str = None
  completed_batch_id: str = None
  completed_batch_qt: float = None
  new_batch_id: str = None
  timestamp: datetime
  user_data: Any


class BatchTimeRecord(FlexModel):
  id: str = Field(None, alias="_id")
  key: str = Field(None, alias="_key")
  batch_id: str
  work_session_id: str
  full_ws: bool = None
  start: datetime
  end: datetime = None



