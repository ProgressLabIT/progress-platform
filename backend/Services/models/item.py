from pydantic import Field

from utils.base_models import FlexModel

# class ProductionItemType(str, Enum):
#   assembly = "assembly"
#   component = "component"
#   comsumable = "consumable"
#   tool = "tool"
#   safety = "safety"

class ProductionItem(FlexModel):
  item_key: str = Field(..., alias="_key")
  code: str
  description: str
  type: str = None
