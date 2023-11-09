from enum import Enum
from typing import List, Optional, Union

from pydantic import Field

from utils.base_models import FlexModel, ArangoDocument



class ReleaseStyle(str, Enum):
  CONTINUOUS = 'continuous'
  BATCH = 'batch'
  SESSION = 'session'
  MANUAL = 'manual'
  JOB = 'job'

class WIPAccess(str, Enum):
  LINE = 'line'
  BUFFER = 'buffer'

class PhaseParameters(FlexModel):
  parallel_job_allowed: bool = True
  step_check: bool = False
  step_check_force_order: bool = False
  production_batch_qt: int = 1 # 0 means the whole job at once
  max_offline: int = 60 # seconds
  auto_new_batch: bool = True
  std_processing_time: int = 60 # seconds
  unsupervised_work_allowed: bool = False
  # release_style: ReleaseStyle = ReleaseStyle.JOB
  # release_batch_qt: int = 1
  # wip_flow: WIPFlow = WIPFlow.BUFFER


class Operation(ArangoDocument):
  name: str
  code: str = None
  description: str = None
  default_phase_parameters: PhaseParameters = PhaseParameters()
  default_phase_notes: str = None


class StepType(str, Enum):
  INSTRUCTION = 'instruction'
  FORM = 'form'
  CHECKLIST = 'checklist'


class FieldType(str, Enum):
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


class PhaseRecord(ArangoDocument):
  alias: str
  description: str = None
  product_key: str
  operation_key: str
  operation_name: str = None
  params: PhaseParameters = PhaseParameters()
  step_sequence: List[Optional[str]] = []
  production_notes: str = None

class PhaseData(PhaseRecord):
  steps: List[Step] = []


class ProcessUpdate(FlexModel):
  # this is the output model for the event logging (after DB update)
  product_key: str = Field(..., alias='_key')
  process_phases: List[str] = None
  new_phases: List[str] = None
  deleted_phases: List[str]
  phase_data: List[PhaseRecord] = None
  step_data: List[Step] = None
