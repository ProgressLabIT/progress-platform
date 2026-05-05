from typing import Any

from pydantic import Field, field_validator

from models.base_models import FlexModel

class BomLineConsumptionOptions(FlexModel):
  consumption_position_key: str | None = Field(None, description="ArangoDB _key of the inventory position from which this component is consumed.", examples=["pos-002"])
  consumption_position_mandatory: bool | None = Field(False, description="When true, operators must select a consumption position before recording usage.", examples=[False])
  minimum_quantity_if_negative: bool | None = Field(False, description="Allow consuming below zero inventory when the position would go negative.", examples=[False])
  minimum_quantity: float | None = Field(None, description="Minimum quantity that must be consumed per unit; null means no lower bound.", examples=[1.0])

class BomLineRead(FlexModel):
  component_key: str = Field(..., description="ArangoDB _key of the component product.", examples=["prod-002"])
  bom_line_key: str = Field(..., description="ArangoDB _key of the BoM line edge in the 'requires' collection.", examples=["bom-line-001"])
  component_code: str = Field(..., description="Product code of the component.", examples=["PROD-B-001"])
  component_description: str = Field(..., description="Description of the component product.", examples=["M5 hex bolt, stainless steel"])
  qt: float = Field(..., description="Required quantity of this component per parent unit.", examples=[4.0])
  phase_key: str | None = Field(None, description="ArangoDB _key of the phase at which this component is consumed; null means any phase.", examples=["phase-001"])
  phase_name: str | None = Field(None, description="Human-readable name of the consumption phase.", examples=["Assembly"])
  # traceability_mandatory: bool | None = False
  traceability_level: str | None = Field(None, description="Traceability level required for this component during consumption.", examples=["form_only"])
  consumption_options: BomLineConsumptionOptions | None = Field(default_factory=BomLineConsumptionOptions, description="Consumption behaviour options for this BoM line.")
  extra: Any = Field(None, description="Arbitrary additional data for external integrations (e.g. ERP line reference).", examples=[None])

  @field_validator('consumption_options', mode='before')
  @classmethod
  def validate_consumption_options(cls, v):
    if v is None:
      return BomLineConsumptionOptions()
    return v


class WOBomLineInput(FlexModel):
  component_key: str = Field(..., description="ArangoDB _key of the component product to consume.", examples=["prod-002"])
  qt: float = Field(..., description="Quantity to consume for this work order line.", examples=[4.0])
  phase_key: str | None = Field(None, description="ArangoDB _key of the phase at which this component is consumed.", examples=["phase-001"])
  consumption_options: BomLineConsumptionOptions | None = Field(default_factory=BomLineConsumptionOptions, description="Consumption behaviour options for this work order BoM line.")
  extra: Any = Field(None, description="Arbitrary additional data for external integrations.", examples=[None])

class WOBomLine(FlexModel):
  component_key: str = Field(..., description="ArangoDB _key of the component product.", examples=["prod-002"])
  component_code: str = Field(..., description="Product code of the component.", examples=["PROD-B-001"])
  component_description: str = Field(..., description="Description of the component product.", examples=["M5 hex bolt, stainless steel"])
  qt: float = Field(..., description="Required quantity of this component per parent unit.", examples=[4.0])
  phase_key: str | None = Field(None, description="ArangoDB _key of the consumption phase.", examples=["phase-001"])
  phase_name: str | None = Field(None, description="Human-readable name of the consumption phase.", examples=["Assembly"])
  consumption_options: BomLineConsumptionOptions | None = Field(default_factory=BomLineConsumptionOptions, description="Consumption behaviour options for this work order BoM line.")
  traceability_level: str | None = Field(None, description="Traceability level required for this component.", examples=["form_only"])
  extra: Any = Field(None, description="Arbitrary additional data.", examples=[None])


class BomLineWriteIn(FlexModel):
  bom_line_key: str | None = Field(None, description="Existing BoM line _key; null for new lines.", examples=["bom-line-001"])
  component_key: str | None = Field(None, description="ArangoDB _key of the component product; required when component_code is not provided.", examples=["prod-002"])
  component_code: str | None = Field(None, description="Product code of the component; used when by_code=true on the endpoint.", examples=["PROD-B-001"])
  qt: float = Field(..., description="Required quantity of this component per parent unit.", examples=[2.0])
  phase_key: str | None = Field(None, description="ArangoDB _key of the phase this component is assigned to; null assigns to the last phase.", examples=["phase-001"])
  type: str = Field('BomLine', description="Edge type stored in the 'requires' collection; always 'BomLine' for BoM lines.", examples=["BomLine"])
  # traceability_mandatory: bool | None = None
  traceability_level: str | None = Field(None, description="Traceability level required for this component.", examples=["form_only"])
  consumption_options: BomLineConsumptionOptions | None = Field(None, description="Consumption behaviour options for this BoM line.")
  extra: Any = Field(None, description="Arbitrary additional data for external integrations.", examples=[None])

class BomLineWriteOut(FlexModel):
  component_id: str = Field(..., alias="_to", description="ArangoDB _id of the component product document (e.g. 'Product/prod-002').", examples=["Product/prod-002"])
  qt: float = Field(..., description="Required quantity of this component per parent unit.", examples=[2.0])
  # traceability_mandatory: bool | None = None
  traceability_level: str | None = Field(None, description="Traceability level required for this component.", examples=["form_only"])
  consumption_options: BomLineConsumptionOptions | None = Field(None, description="Consumption behaviour options for this BoM line.")
  phase_id: str = Field(..., alias="_from", description="ArangoDB _id of the Phase document this BoM line is attached to (e.g. 'Phase/phase-001').", examples=["Phase/phase-001"])
  type: str = Field('BomLine', description="Edge type in the 'requires' collection.", examples=["BomLine"])
  extra: Any = Field(None, description="Arbitrary additional data.", examples=[None])
