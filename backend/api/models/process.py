from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field, BaseModel

from models.print import PrintTemplateRecord
from models.form import FormFieldDefinition
from models.base_models import FlexModel, ArangoDocument
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
  display_job_timer: bool = False
  # release_style: ReleaseStyle = ReleaseStyle.JOB
  # release_batch_qt: int = 1
  # wip_flow: WIPFlow = WIPFlow.BUFFER


class StepType(str, Enum):
  INSTRUCTION = 'instruction'
  FORM = 'form'


# TODO: Split into StepDefinition(to be used in operation default steps) and Step(to be used in process phases)
class Step(FlexModel):
  key: str | None = Field(None, alias="_key")
  title: str | None = None
  description: str | None = None
  type: StepType = StepType.INSTRUCTION
  form_fields: List[FormFieldDefinition] = []
  # TODO: Stop saving print_templates as part of Step (only valid for default step definitions)
  print_templates: List[str | PrintTemplateRecord] = []


# TODO: Add validation for size, content_type, etc.
class Media(ArangoDocument):
  name: str
  size: int
  content_type: str
  # TODO: Address serialization warning (Expected `datetime` but got `str` - serialized value may not be as expected)
  created_at: datetime = Field(default_factory=timestamp)


class StepWithMediaInfo(Step):
  # TODO: Address serialization warning (Expected `Union[str, Media]` but got `Media` - serialized value may not be as expected)
  media: list[str | Media] = []

class Operation(ArangoDocument):
  name: str
  code: str | None = None
  description: str | None = None
  default_phase_parameters: PhaseParameters = PhaseParameters()
  default_phase_notes: str | None = None
  default_phase_steps: List[StepWithMediaInfo] = []


class PhaseRecord(ArangoDocument):
  alias: str
  product_key: str # TODO: consider stopping storing this. The existing ProductPhase relationship in 'requires' can be used instead. Split the model to have the property only when needed.
  operation_key: str # TODO: consider stopping storing this. The existing PhaseOperation relationship in 'requires' can be used instead. Split the model to have the property only when needed.
  params: PhaseParameters = PhaseParameters()
  step_sequence: List[Optional[str]] = []
  production_notes: str | None = None

class PhaseData(PhaseRecord):
  steps: List[Step] = []
  print_templates: List[PrintTemplateRecord] = []


# TODO: this is not used anywhere, consider removing
class ProcessUpdate(FlexModel):
  # this is the output model for the event logging (after DB update)
  product_key: str = Field(..., alias='_key')
  process_phases: list[str] | None = None
  new_phases: list[str] | None = None
  deleted_phases: List[str]
  phase_data: list[PhaseRecord] | None = None
  step_data: list[Step] | None = None

class ProcessTaskDefinition(BaseModel):
  task_type_key: str
  task_name: str
  task_description: str | None = None
  before_phase: str | None = None
  after_phase: str | None = None
