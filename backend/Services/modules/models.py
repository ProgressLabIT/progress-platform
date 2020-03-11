from typing import List, Optional
from pydantic import BaseModel, Field, ByteSize
from enum import Enum
from random import randrange, uniform

class FlexModel(BaseModel):
  class Config:
    allow_population_by_field_name = True


# ==================================
# PRODUCT
# ==================================

# class ProductBase(BaseModel):
#   code: str
#   description: Optional[str] = None

# class ProductListItem(ProductBase):
#   """ 
#   Represents the subset of the Product DB schema necessary 
#   for use in the product list view
#   """

#   # the _key field must be aliased because pydantic will not 
#   # accept fields with leading underscore
#   key: str = Field(..., alias="_key")
#   active: bool = True
#   trash: bool = False


class TargetAverageCost(BaseModel):
  target: float = randrange(500, 120000, 100)
  average: float = target * (1 + uniform(-0.2, 0.2))


class TargetAverageTime(TargetAverageCost):
  target: float = randrange(900000, 216000000, 705267)
  average: float = target * (1 + uniform(-0.2, 0.2))


class ProductData(FlexModel):
  key: str = Field(None, alias="_key")
  code: str
  description: Optional[str] = None
  active: bool = True
  trash: bool = False
  cost: TargetAverageCost = TargetAverageCost()
  # sale_price: float = 0
  # margin: TargetAverageData = TargetAverageData()
  technical_batch_qt: int = 0
  # economic_order_qt: int = 0   ----> Doesn't make sense in a MTO/ATO context: only for purchases or MTS
  minimum_order_qt: int = 0
  # tags: List[str] = []
  process_phases: List[str] = [] 
  lead_time: TargetAverageTime = TargetAverageTime()
  throughput_time: TargetAverageTime = TargetAverageTime()
  processing_time: TargetAverageTime = TargetAverageTime()

class ProductDoc(BaseModel):
  name: str
  size: ByteSize

class ProductFull(ProductData):
  docs: List[ProductDoc] = []
  img_name: str = None

# ==================================
# ITEMS AND BOM
# ==================================

# class ProductionItemType(str, Enum):
#   assembly = "assembly"
#   component = "component"
#   comsumable = "consumable"
#   tool = "tool"
#   safety = "safety"

class ProductionItem(FlexModel):
  item_id: str = Field(..., alias="_id")
  code: str
  description: str
  type: str = None

class BomItemRead(BaseModel):
  item_id: str
  rel_id: str
  phase_id: str = None
  code: str
  description: str
  type: str = None
  phase_name: str = None
  qt: float

class BomItemWrite(BaseModel):
  item_id: str = Field(..., alias="_to")
  qt: float
  phase_id: str = Field(..., alias="_from")
  rel_type: str = 'BomItem'
  rel_id: str = Field(None, alias="_id")
  class Config:
    allow_population_by_field_name = True

# ==================================
# PROCESS
# ==================================

class StepCheck(Enum):
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

class PhaseParameters(BaseModel):
  parallel_job_allowed: bool = True
  step_check: StepCheck = StepCheck.SINGLE
  step_check_force_order: bool = False
  release_style: ReleaseStyle = ReleaseStyle.JOB
  production_batch_qt: int = 1
  release_batch_qt: int = 1
  # wip_flow: WIPFlow = WIPFlow.BUFFER

class StepType(Enum):
  INSTRUCTION = 'instruction'
  FORM = 'form'
  CHECKLIST = 'checklist'

class FieldType(Enum):
  SHORT = 'short'
  LONG = 'long'

class InputField(BaseModel):
  type: FieldType = 'short'
  name: str = None
  # Add mandatory flag and field description

class Step(FlexModel):
  id: str = Field(None, alias="_id")
  title: str = None
  description: str = None
  type: StepType = StepType.INSTRUCTION
  checks: List[str] = []
  input_fields: List[InputField] = []

class Media(BaseModel):
  name: str

class StepWithMediaInfo(Step):
  media: List[Media] = None


class PhaseProcedure(FlexModel):
  id: str = Field(None, alias="_id")
  alias: str
  description: str = None
  operation_id: str = None
  steps: List[Step] = []
  params: PhaseParameters = PhaseParameters()
  std_processing_time: int = 0 # in milliseconds

class PhaseUpdate(PhaseProcedure):
  step_sequence: List[Optional[str]] = []

class ProcessUpdate(BaseModel):
  # this is the output model for the event logging (after DB update)
  product_key: str = Field(..., alias='_key')
  process_phases: List[str] = None
  new_phases: List[str] = None
  deleted_phases: List[str]
  phase_data: List[PhaseUpdate] = None
  step_data: List[Step] = None
