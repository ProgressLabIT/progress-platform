from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field

from models.print import PrintTemplateRecord
from models.form import FormFieldDefinition
from utils.base_models import FlexModel, ArangoDocument
from utils.dt import timestamp


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


class StepType(str, Enum):
  INSTRUCTION = 'instruction'
  FORM = 'form'


class Step(FlexModel):
  key: str = Field(None, alias="_key")
  title: str = None
  description: str = None
  type: StepType = StepType.INSTRUCTION
  form_fields: List[FormFieldDefinition] = []
  print_templates: List[PrintTemplateRecord | str] = []


# TODO: Add validation for size, content_type, etc.
class Media(ArangoDocument):
  name: str
  size: int
  content_type: str
  created_at: datetime = Field(default_factory=timestamp)


class StepWithMediaInfo(Step):
  media: List[Media | str] = None

class Operation(ArangoDocument):
  name: str
  code: str = None
  description: str = None
  default_phase_parameters: PhaseParameters = PhaseParameters()
  default_phase_notes: str = None
  default_phase_steps: List[StepWithMediaInfo] = []


class PhaseRecord(ArangoDocument):
  alias: str
  product_key: str
  operation_key: str
  params: PhaseParameters = PhaseParameters()
  step_sequence: List[Optional[str]] = []
  production_notes: str = None

class PhaseData(PhaseRecord):
  steps: List[Step] = []
  print_templates: List[PrintTemplateRecord] = []


class ProcessUpdate(FlexModel):
  # this is the output model for the event logging (after DB update)
  product_key: str = Field(..., alias='_key')
  process_phases: List[str] = None
  new_phases: List[str] = None
  deleted_phases: List[str]
  phase_data: List[PhaseRecord] = None
  step_data: List[Step] = None
