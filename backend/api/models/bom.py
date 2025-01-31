from typing import Any

from pydantic import Field

from models.base_models import FlexModel

class BomLineConsumptionOptions(FlexModel):
  preferred_position_key: str | None = None
  preferred_position_mandatory: bool | None = None
  all_or_minimum_in_case_negative: bool | None = None
  mandatory_quantity: float | None = None

class BomLineRead(FlexModel):
  component_key: str
  bom_line_key: str
  component_code: str
  component_description: str
  qt: float
  phase_key: str | None = None
  phase_name: str | None = None
  traceability_mandatory: bool | None = False
  traceability_level: str | None = None
  consumption_options: BomLineConsumptionOptions | None = None
  extra: Any = None


class BomLineWriteIn(FlexModel):
  component_key: str | None = None
  component_code: str | None = None
  qt: float
  phase_key: str | None = None
  type: str = 'BomLine'
  traceability_mandatory: bool | None = None
  traceability_level: str | None = None
  consumption_options: BomLineConsumptionOptions | None = None
  extra: Any = None

class BomLineWriteOut(FlexModel):
  component_id: str = Field(..., alias="_to")
  qt: float
  traceability_mandatory: bool | None = None
  traceability_level: str | None = None
  consumption_options: BomLineConsumptionOptions | None = None
  phase_id: str = Field(..., alias="_from")
  type: str = 'BomLine'
  extra: Any = None

