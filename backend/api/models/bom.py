from enum import Enum
from pydantic import Field

from commons.models.base_models import FlexModel, ArangoDocument


class BomLineRead(FlexModel):
  component_key: str
  bom_line_key: str
  phase_key: str | None = None
  component_code: str
  component_description: str
  phase_name: str | None = None
  qt: float
  traceability_mandatory: bool | None = None
  traceability_level: str | None = None


class BomLineWriteIn(FlexModel):
  component_key: str | None = None
  component_code: str | None = None
  qt: float
  phase_key: str | None = None
  type: str = 'BomLine'
  traceability_mandatory: bool | None = None
  traceability_level: str | None = None

class BomLineWriteOut(FlexModel):
  component_id: str = Field(..., alias="_to")
  qt: float
  traceability_mandatory: bool | None = None
  traceability_level: str | None = None
  phase_id: str = Field(..., alias="_from")
  type: str = 'BomLine'
