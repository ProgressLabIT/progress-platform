from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class FlexModel(BaseModel):
  class Config:
    allow_population_by_field_name = True


# ==================================
# PRODUCT
# ==================================

class ProductBase(BaseModel):
  code: str
  description: Optional[str] = None

class ProductListItem(ProductBase):
  """ 
  Represents the subset of the Product DB schema necessary 
  for use in the product list view
  """

  # the _key field must be aliased because pydantic will not 
  # accept fields with leading underscore
  key: str = Field(..., alias="_key")
  active: bool = True
  trash: bool = False


class TargetAverageData(BaseModel):
  target: float = 0
  average: float = 0

class ProductFull(ProductBase):
  """
  Extends the ProductBase class to represents 
  the full DB schema of the product
  """
  active: bool = True
  trash: bool = False
  cost: TargetAverageData = TargetAverageData()
  sale_price: float = 0
  margin: TargetAverageData = TargetAverageData()
  technical_batch_qt: float = 0
  economic_order_qt: float = 0
  minimum_order_qt: float = 0
  tags: List[str] = []
  process_phases: List[str] = [] 



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
  phase_id: str
  code: str
  description: str
  type: str = None
  phase_name: str
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

class InputFieldType(str, Enum):
  short = "short"
  long = "long"

class InputField(BaseModel):
  type: InputFieldType
  name: str = None

class Step(BaseModel):
  key: str = Field(..., alias="_key")
  title: str
  description: str = None
  type: str
  checks: List[str] = []
  input_fields: List[InputField] = []


class PhaseData(BaseModel):
  id: str = Field(..., alias="_id")
  alias: str
  description: str = None
  steps: List[Step] = []


class PhaseSequence(BaseModel):
  product_key: str = Field(..., alias='_key')
  process_phases: List[str]
