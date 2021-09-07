from enum import Enum

from pydantic import Field

from utils.base_models import FlexModel

class ProductionItemType(Enum):
  ASSEMBLY = "assembly"
  COMPONENT = "component"
  COMSUMABLE = "consumable"
  TOOL = "tool"
  SAFETY = "safety"

class ProductionItem(FlexModel):
  item_key: str = Field(..., alias="_key")
  code: str
  description: str
  type: ProductionItemType = None
  value: float = None
