from datetime import datetime
from enum import Enum
from random import randrange, uniform
from typing import Any, List, Optional, Literal

from pydantic import BaseModel, ByteSize, ConfigDict, Field

from models.base_models import FlexModel
from models.tag import Tag
from models.counter import Counter
from utils.search import WildcardString



class TargetAverageCost(FlexModel):
  target: float = randrange(500, 120000, 100)
  average: float = target * (1 + uniform(-0.2, 0.2))


class TargetAverageTime(TargetAverageCost):
  target: float = randrange(900000, 216000000, 705267)
  average: float = target * (1 + uniform(-0.2, 0.2))


class KPIWindowType(str, Enum):
  TIME = 'time'
  COUNT = 'count'

class TraceabilityLevel(str, Enum):
  FORM_ONLY = 'form_only'
  COMPLETE = 'complete'


class ProductBaseData(FlexModel):
  key: str | None = Field(None, alias="_key", description="ArangoDB document key.", examples=["prod-001"])
  code: str = Field(..., description="Unique product code used across the manufacturing system.", examples=["PROD-A-001"])
  description: str | None = Field(None, description="Human-readable description of the product.", examples=["Aluminium bracket, anodised black, 50x30mm"])
  active: bool | None = Field(True, description="Whether this product is active in the catalogue.", examples=[True])
  image: bool | None = Field(False, description="True if a product image file (image.jpg) exists in the product media folder.", examples=[False])
  tags: List[Tag] | None = Field([], description="Tags attached to this product for filtering and categorisation.")
  counter_key: str | None = Field(None, description="ArangoDB _key of the Counter used to generate serial numbers for this product.", examples=["counter-001"])
  traceability_level: TraceabilityLevel | None = Field(None, description="Traceability tracking level: 'form_only' captures form data only; 'complete' enables full serial traceability.", examples=["form_only"])
  manage_inventory: bool | None = Field(False, description="Whether inventory movements are tracked for this product.", examples=[False])
  allow_negative_inventory: bool | None = Field(False, description="Allow inventory to go negative (e.g. for consumption before replenishment).", examples=[False])
  serial_code_on_creation: bool | None = Field(False, description="Automatically generate a serial code when a work order for this product is created.", examples=[False])


class ProductMetadataField(BaseModel):
  custom_field_key: str = Field(..., description="ArangoDB _key of the CustomField definition this metadata entry maps to.", examples=["cf-001"])
  value: Any = Field(None, description="Value for this custom field instance on the product.", examples=["RAL 9005"])
  label: str | None = Field(None, description="Display label override for this field on this product; falls back to custom field default_label.", examples=["Surface Colour"])
  hint: str | None = Field(None, description="Hint text override for this field on this product; falls back to custom field default_hint.", examples=["Select the RAL colour code"])

class ProductDetails(ProductBaseData):
  trash: bool = Field(False, description="Soft-delete flag; true means the product is in the trash and excluded from active listings.", examples=[False])

  created: datetime | None = Field(None, description="UTC timestamp when this product was created.", examples=["2026-01-10T09:00:00"])
  updated: datetime | None = Field(None, description="UTC timestamp of the last update to this product.", examples=["2026-03-22T14:30:00"])

  cost: TargetAverageCost = Field(default_factory=TargetAverageCost, description="Target and rolling-average cost figures for this product.")
  # sale_price: float = 0
  # margin: TargetAverageData = TargetAverageData()
  technical_batch_qt: int = Field(0, description="Technical batch quantity — the standard lot size for manufacturing planning.", examples=[10])
  # economic_order_qt: int = 0   ----> Doesn't make sense in a MTO/ATO context: only for purchases or MTS
  minimum_order_qt: int = Field(0, description="Minimum order quantity enforced when creating work orders for this product.", examples=[1])
  # tags: List[str] = []
  process_phases: List[str] = Field([], description="Ordered list of Phase _keys constituting this product's production process.", examples=[["phase-001", "phase-002"]])
  production_notes: str | None = Field(None, description="Free-text notes displayed to operators during production for this product.", examples=["Use calibrated torque wrench — see WI-042."])

  throughput_time_target: float | None = Field(None, description="Target throughput time in seconds from order release to completion.", examples=[86400.0])
  processing_time_target: float | None = Field(None, description="Target net processing time per unit in seconds.", examples=[3600.0])

  kpi_window_size: int | None = Field(None, description="KPI rolling window size: number of days if kpi_window_type='time', number of work orders if 'count'.", examples=[30])
  kpi_window_type: Optional[KPIWindowType] = Field(KPIWindowType.COUNT, description="Unit for the KPI rolling window: 'time' (days) or 'count' (work orders).", examples=["count"])

  metadata: List[ProductMetadataField] | None = Field(None, description="List of custom metadata fields and their values for this product.")

  default_production_position_key: str | None = Field(None, description="ArangoDB _key of the default inventory position where finished goods are deposited.", examples=["pos-001"])
  default_consumption_position_key: str | None = Field(None, description="ArangoDB _key of the default inventory position from which components are consumed.", examples=["pos-002"])

class ProductDoc(FlexModel):
  name: str = Field(..., description="Filename of the document in the product doc folder.", examples=["assembly-drawing-rev-c.pdf"])
  size: ByteSize = Field(..., description="File size.", examples=[204800])

class ProductFull(ProductDetails):
  docs: List[ProductDoc] = Field([], description="List of document files attached to this product.")
  img_name: str | None = Field(None, description="Filename of the product image if one exists.", examples=["image.jpg"])
  counter: Counter | None = Field(None, description="Resolved Counter document if counter_key is set.")


class ProductSearchParams(BaseModel):
  search_string: WildcardString = Field(None, description="Wildcard search string matched against product code (and description when search_description=true).", examples=["PROD-A-*"])
  search_description: bool = Field(False, description="Extend the search_string match to the product description field.", examples=[False])
  tag_key: str | None = Field(None, description="Filter products that have this tag _key attached.", examples=["tag-001"])
  include_text: WildcardString = Field(None, description="Only return products whose code contains this substring.", examples=["BRACKET"])
  exclude_text: WildcardString = Field(None, description="Exclude products whose code contains this substring.", examples=["OBSOLETE"])
  include_tags: list[str] | None = Field(None, description="List of tag _keys; only products having these tags are returned.", examples=[["tag-001", "tag-002"]])
  exclude_tags: list[str] | None = Field(None, description="List of tag _keys; products having any/all of these tags are excluded.", examples=[["tag-archived"]])
  include_tags_operator: Literal["ALL", "ANY"] = Field("ALL", description="Whether all or any of include_tags must match.", examples=["ALL"])
  exclude_tags_operator: Literal["ALL", "ANY"] = Field("ANY", description="Whether all or any of exclude_tags must match to trigger exclusion.", examples=["ANY"])
  has_operation_key: str | None = Field(None, description="Filter products whose process includes a phase with this operation _key.", examples=["op-001"])
  active_only: bool = Field(True, description="When true, only active (non-trashed) products are returned.", examples=[True])
  traceability_only: bool = Field(False, description="When true, only products with a non-null traceability_level are returned.", examples=[False])
  details: bool = Field(False, description="Return full ProductDetails instead of lightweight ProductBaseData.", examples=[False])
  limit: None | int = Field(None, description="Maximum number of results to return; null returns all matching products.", examples=[100])
  offset: int = Field(0, description="Number of results to skip for pagination.", examples=[0])


class ImportRowResult(BaseModel):
    """Per-row classification returned in dry-run response rows[]."""
    row: int
    code: str
    action: str  # 'create' | 'update' | 'error' | 'skipped'
    errors: list[str] = Field(default_factory=list)


class ImportDryRunResponse(BaseModel):
    """Enriched dry-run response — carries per-row rows[] alongside aggregate counts."""
    model_config = ConfigDict(populate_by_name=True)
    status: str
    file_key: str
    filename: str
    rows_total: int
    created_count: int
    updated_count: int
    skipped_count: int = 0
    error_count: int
    ignored_columns: list[str] = Field(default_factory=list)
    rows: list[ImportRowResult] = Field(default_factory=list)
