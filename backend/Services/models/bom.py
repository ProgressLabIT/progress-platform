from pydantic import Field

from utils.base_models import FlexModel


class BomItemRead(FlexModel):
  item_id: str
  rel_id: str
  phase_id: str = None
  code: str
  description: str
  type: str = None
  phase_name: str = None
  qt: float



class BomItemWrite(FlexModel):
  item_id: str = Field(..., alias="_to")
  qt: float
  phase_id: str = Field(..., alias="_from")
  rel_type: str = 'BomItem'
  rel_id: str = Field(None, alias="_id")