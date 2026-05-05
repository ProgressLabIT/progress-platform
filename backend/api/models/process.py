from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import Field

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
  parallel_job_allowed: bool = Field(
    True,
    description="Allow multiple jobs to run simultaneously on this phase.",
    examples=[True],
  )
  step_check: bool = Field(
    False,
    description="Require operators to complete all steps before closing a batch.",
    examples=[False],
  )
  step_check_force_order: bool = Field(
    False,
    description="When step_check is enabled, force steps to be completed in sequence.",
    examples=[False],
  )
  production_batch_qt: int = Field(
    1,
    description="Number of units per production batch. 0 means the whole job at once.",
    examples=[1],
  )
  max_offline: int = Field(
    60,
    description="Maximum seconds a workstation can be offline before the session is flagged.",
    examples=[60],
  )
  auto_new_batch: bool = Field(
    True,
    description="Automatically open a new batch when the previous one is completed.",
    examples=[True],
  )
  std_processing_time: int = Field(
    60,
    description="Standard processing time per unit in seconds, used for KPI target calculations.",
    examples=[60],
  )
  unsupervised_work_allowed: bool = Field(
    False,
    description="Allow production work to proceed without a supervisor logged in.",
    examples=[False],
  )
  display_job_timer: bool = Field(
    False,
    description="Show a running timer on the operator UI for the current job.",
    examples=[False],
  )
  # release_style: ReleaseStyle = ReleaseStyle.JOB
  # release_batch_qt: int = 1
  # wip_flow: WIPFlow = WIPFlow.BUFFER


class StepType(str, Enum):
  INSTRUCTION = 'instruction'
  FORM = 'form'


# TODO: Split into StepDefinition(to be used in operation default steps) and Step(to be used in process phases)
class Step(FlexModel):
  key: str | None = Field(None, alias="_key", description="ArangoDB document key.", examples=["step-001"])
  title: str | None = Field(None, description="Short display title for the step.", examples=["Inspect weld joints"])
  description: str | None = Field(None, description="Full markdown-formatted step instructions.", examples=["Check all weld joints for porosity defects per IPC-A-610."])
  type: StepType = Field(StepType.INSTRUCTION, description="Step category: 'instruction' for informational steps, 'form' for data-capture steps.", examples=["instruction"])
  form_fields: List[FormFieldDefinition] = Field(
    [],
    description="Ordered list of form field definitions rendered when type='form'.",
    examples=[[]],
  )
  # TODO: Stop saving print_templates as part of Step (only valid for default step definitions)
  print_templates: List[str | PrintTemplateRecord] = Field(
    [],
    description="Print templates available at this step, either as _key strings or resolved PrintTemplateRecord objects.",
    examples=[[]],
  )


# TODO: Add validation for size, content_type, etc.
class Media(ArangoDocument):
  name: str = Field(..., description="Original filename of the uploaded media file.", examples=["weld-diagram.png"])
  size: int = Field(..., description="File size in bytes.", examples=[204800])
  content_type: str = Field(..., description="MIME type of the media file.", examples=["image/png"])
  # TODO: Address serialization warning (Expected `datetime` but got `str` - serialized value may not be as expected)
  created_at: datetime = Field(default_factory=timestamp, description="UTC timestamp when the media record was created.", examples=["2026-01-15T08:30:00"])


class StepWithMediaInfo(Step):
  # TODO: Address serialization warning (Expected `Union[str, Media]` but got `Media` - serialized value may not be as expected)
  media: list[str | Media] = Field(
    [],
    description="Media files attached to this step, either as _key strings or resolved Media objects.",
    examples=[[]],
  )

class Operation(ArangoDocument):
  name: str = Field(..., description="Human-readable name for this operation template.", examples=["Surface Inspection"])
  code: str | None = Field(None, description="Optional short code identifying this operation.", examples=["OP-INSPECT-01"])
  description: str | None = Field(None, description="Detailed description of the operation purpose and scope.", examples=["Visual and dimensional inspection of machined surfaces."])
  default_phase_parameters: PhaseParameters = Field(
    default_factory=PhaseParameters,
    description="Default phase execution parameters applied when this operation is assigned to a product phase.",
  )
  default_phase_notes: str | None = Field(None, description="Default production notes pre-populated on phases using this operation.", examples=["Refer to drawing REV-C for tolerance callouts."])
  default_phase_steps: List[StepWithMediaInfo] = Field(
    [],
    description="Default step sequence copied to product phases when this operation is applied.",
    examples=[[]],
  )


class PhaseRecord(ArangoDocument):
  alias: str = Field(..., description="Human-readable name for this phase in the context of its product.", examples=["Assembly"])
  product_key: str = Field(..., description="ArangoDB _key of the product this phase belongs to.", examples=["prod-001"])  # TODO: consider stopping storing this. The existing ProductPhase relationship in 'requires' can be used instead. Split the model to have the property only when needed.
  operation_key: str = Field(..., description="ArangoDB _key of the Operation template this phase is based on.", examples=["op-001"])  # TODO: consider stopping storing this. The existing PhaseOperation relationship in 'requires' can be used instead. Split the model to have the property only when needed.
  params: PhaseParameters = Field(
    default_factory=PhaseParameters,
    description="Phase execution parameters that override the operation defaults for this specific product.",
  )
  step_sequence: List[Optional[str]] = Field(
    [],
    description="Ordered list of Step _keys defining the step execution order for this phase.",
    examples=[["step-001", "step-002"]],
  )
  production_notes: str | None = Field(None, description="Free-text production notes displayed to operators during this phase.", examples=["Verify torque values before proceeding to next phase."])

class PhaseData(PhaseRecord):
  steps: List[Step] = Field(
    [],
    description="Fully resolved Step objects for this phase, ordered by step_sequence.",
    examples=[[]],
  )
  print_templates: List[PrintTemplateRecord] = Field(
    [],
    description="Print templates available at the phase level.",
    examples=[[]],
  )


# TODO: this is not used anywhere, consider removing
class ProcessUpdate(FlexModel):
  # this is the output model for the event logging (after DB update)
  product_key: str = Field(..., alias='_key', description="ArangoDB _key of the product whose process was updated.", examples=["prod-001"])
  process_phases: list[str] | None = Field(None, description="New ordered list of Phase _keys.", examples=[["phase-001", "phase-002"]])
  new_phases: list[str] | None = Field(None, description="Phase _keys that were inserted during this update.", examples=[["phase-003"]])
  deleted_phases: List[str] = Field(..., description="Phase _keys that were removed during this update.", examples=[["phase-old-001"]])
  phase_data: list[PhaseRecord] | None = Field(None, description="Full PhaseRecord objects for the updated phases.", examples=[[]])
  step_data: list[Step] | None = Field(None, description="Full Step objects for the updated steps.", examples=[[]])
