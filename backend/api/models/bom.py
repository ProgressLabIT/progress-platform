from enum import Enum
from pydantic import Field

from utils.base_models import ArangoDocument


class BomLineRead(ArangoDocument):
  product_key: str
  bom_line_key: str
  phase_key: str = None
  product_code: str
  product_description: str
  phase_name: str = None
  qt: float


class BomLineWriteIn(ArangoDocument):
  product_key: str
  qt: float
  phase_key: str
  type: str = 'BomLine'

class BomLineWriteOut(ArangoDocument):
  product_id: str = Field(..., alias="_to")
  qt: float
  phase_id: str = Field(..., alias="_from")
  type: str = 'BomLine'
