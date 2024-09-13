from typing import Any

from pydantic import Field

from models.base_models import FlexModel


class BomLineRead(FlexModel):
  component_key: str
  bom_line_key: str
  component_code: str
  component_description: str
  qt: float
  ext_key: Any = None
  phase_key: str | None = None
  phase_name: str | None = None
  traceability_mandatory: bool | None = False
  traceability_level: str | None = None



class BomLineWriteIn(FlexModel):
  component_key: str | None = None
  component_code: str | None = None
  qt: float
  phase_key: str | None = None
  type: str = 'BomLine'
  traceability_mandatory: bool | None = None
  traceability_level: str | None = None
  ext_key: Any = None

class BomLineWriteOut(FlexModel):
  component_id: str = Field(..., alias="_to")
  qt: float
  traceability_mandatory: bool | None = None
  traceability_level: str | None = None
  phase_id: str = Field(..., alias="_from")
  type: str = 'BomLine'
  ext_key: Any = None