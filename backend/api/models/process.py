from enum import Enum
from typing import List, Optional, Union

from pydantic import Field

from utils.base_models import FlexModel, ArangoDocument




class StepCheckBatch(Enum):
  NONE = 'none'
  SINGLE = 'single'
  FIXED_BATCH = 'fixed_batch'
  MANUAL_BATCH = 'manual_batch'
  JOB = 'job'

class ReleaseStyle(Enum):
  CONTINUOUS = 'continuous'
  BATCH = 'batch'
  SESSION = 'session'
  MANUAL = 'manual'
  JOB = 'job'

class WIPAccess(Enum):
  LINE = 'line'
  BUFFER = 'buffer'

class PhaseParameters(FlexModel):
  parallel_job_allowed: bool = True
  step_check: StepCheckBatch = StepCheckBatch.NONE
  step_check_force_order: bool = False
  production_batch_qt: int = 1
  max_offline: int = 60 # seconds
  # release_style: ReleaseStyle = ReleaseStyle.JOB
  # release_batch_qt: int = 1
  # wip_flow: WIPFlow = WIPFlow.BUFFER


class Operation(ArangoDocument):
  name: str
  code: str = None
  description: str = None
  default_phase_parameters: PhaseParameters = PhaseParameters()


class StepType(Enum):
  INSTRUCTION = 'instruction'
  FORM = 'form'
  CHECKLIST = 'checklist'


class FieldType(Enum):
  SHORT = 'short'
  LONG = 'long'


class InputField(FlexModel):
  type: FieldType = 'short'
  name: str = None
  # Add mandatory flag and field description


class Step(FlexModel):
  key: str = Field(None, alias="_key")
  title: str = None
  description: str = None
  type: StepType = StepType.INSTRUCTION
  checks: List[str] = []
  input_fields: List[InputField] = []


class Media(FlexModel):
  name: str


class StepWithMediaInfo(Step):
  media: List[Union[Media, str]] = None


class PhaseData(FlexModel):
  key: str = Field(None, alias="_key")
  alias: str
  description: str = None
  operation_key: str = None
  operation_name: str = None
  steps: List[Step] = []
  params: PhaseParameters = PhaseParameters()
  std_processing_time: int = 0 # in milliseconds

class PhaseUpdate(PhaseData):
  step_sequence: List[Optional[str]] = []

class ProcessUpdate(FlexModel):
  # this is the output model for the event logging (after DB update)
  product_key: str = Field(..., alias='_key')
  process_phases: List[str] = None
  new_phases: List[str] = None
  deleted_phases: List[str]
  phase_data: List[PhaseUpdate] = None
  step_data: List[Step] = None
