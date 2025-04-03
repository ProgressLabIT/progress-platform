from typing import Any

from pydantic import Field, field_validator

from models.base_models import FlexModel

class BomLineConsumptionOptions(FlexModel):
  consumption_position_key: str | None = None
  consumption_position_mandatory: bool | None = False
  minimum_quantity_if_negative: bool | None = False
  minimum_quantity: float | None = None

class BomLineRead(FlexModel):
  component_key: str
  bom_line_key: str
  component_code: str
  component_description: str
  qt: float
  phase_key: str | None = None
  phase_name: str | None = None
  # traceability_mandatory: bool | None = False
  traceability_level: str | None = None
  consumption_options: BomLineConsumptionOptions | None = Field(default_factory=BomLineConsumptionOptions)
  extra: Any = None

  @field_validator('consumption_options', mode='before')
  @classmethod
  def validate_consumption_options(cls, v):
    if v is None:
      return BomLineConsumptionOptions()
    return v


class WOBomLineInput(FlexModel):
  component_key: str
  qt: float
  phase_key: str | None = None
  extra: Any = None

class WOBomLine(FlexModel):
  component_key: str
  component_code: str
  component_description: str
  qt: float
  phase_key: str | None = None
  phase_name: str | None = None
  consumption_options: BomLineConsumptionOptions | None = Field(default_factory=BomLineConsumptionOptions)
  traceability_level: str | None = None
  extra: Any = None


class BomLineWriteIn(FlexModel):
  bom_line_key: str | None = None
  component_key: str | None = None
  component_code: str | None = None
  qt: float
  phase_key: str | None = None
  type: str = 'BomLine'
  # traceability_mandatory: bool | None = None
  traceability_level: str | None = None
  consumption_options: BomLineConsumptionOptions | None = None
  extra: Any = None

class BomLineWriteOut(FlexModel):
  component_id: str = Field(..., alias="_to")
  qt: float
  # traceability_mandatory: bool | None = None
  traceability_level: str | None = None
  consumption_options: BomLineConsumptionOptions | None = None
  phase_id: str = Field(..., alias="_from")
  type: str = 'BomLine'
  extra: Any = None

