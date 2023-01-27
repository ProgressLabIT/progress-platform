from enum import Enum
from pydantic import Field

from utils.base_models import FlexModel, ArangoDocument


class BomLineRead(FlexModel):
  component_key: str
  bom_line_key: str
  phase_key: str = None
  component_code: str
  component_description: str
  phase_name: str = None
  qt: float


class BomLineWriteIn(ArangoDocument):
  component_key: str
  qt: float
  phase_key: str
  type: str = 'BomLine'

class BomLineWriteOut(ArangoDocument):
  component_id: str = Field(..., alias="_to")
  qt: float
  phase_id: str = Field(..., alias="_from")
  type: str = 'BomLine'
