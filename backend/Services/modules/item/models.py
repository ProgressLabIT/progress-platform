from utils.flex_model import FlexModel
from pydantic import Field

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
