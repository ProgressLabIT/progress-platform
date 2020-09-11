from enum import Enum
from pydantic import Field

from utils.base_models import ArangoDocument



class BomLineType(Enum):
  COMPONENT = 'component'
  ASSEMBLY = 'assembly'
  CONSUMABLE = 'consumable'
  TOOL = 'tool'
  SAFETY = 'safety'


class BomLineRead(ArangoDocument):
  item_key: str
  bom_line_key: str
  phase_key: str = None
  code: str
  description: str
  type: str = None
  phase_name: str = None
  qt: float


class BomLineWriteIn(ArangoDocument):
  item_key: str
  item_type: BomLineType
  qt: float
  phase_key: str
  type: str = 'BomItem'

class BomLineWriteOut(ArangoDocument):
  item_id: str = Field(..., alias="_to")
  qt: float
  phase_id: str = Field(..., alias="_from")
  type: str = 'BomItem'