from datetime import datetime
from enum import Enum
from random import randrange, uniform
from typing import Any, List, Optional, Literal
import re

from pydantic import BaseModel, ByteSize, Field, field_validator

from models.base_models import FlexModel
from models.tag import Tag
from models.counter import Counter
from utils.search import wildcard_to_regex



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
  key: str | None = Field(None, alias="_key")
  code: str
  description: str | None = None
  active: bool | None = True
  image: bool | None = False # to be replaced with Object Storage url in the future
  tags: List[Tag] | None= []
  counter_key: str | None = None
  traceability_level: TraceabilityLevel | None = None
  manage_inventory: bool | None = False
  allow_negative_inventory: bool | None = False
  serial_code_on_creation: bool | None = False


class ProductMetadataField(BaseModel):
  custom_field_key: str # reference to CustomField record
  value: Any = None
  label: str | None = None
  hint: str | None = None

class ProductDetails(ProductBaseData):
  trash: bool = False

  created: datetime | None = None
  updated: datetime | None = None

  cost: TargetAverageCost = TargetAverageCost()
  # sale_price: float = 0
  # margin: TargetAverageData = TargetAverageData()
  technical_batch_qt: int = 0
  # economic_order_qt: int = 0   ----> Doesn't make sense in a MTO/ATO context: only for purchases or MTS
  minimum_order_qt: int = 0
  # tags: List[str] = []
  process_phases: List[str] = []
  production_notes: str | None = None

  throughput_time_target: float | None = None #TargetAverageTime = TargetAverageTime()
  processing_time_target: float | None = None #TargetAverageTime = TargetAverageTime()

  kpi_window_size: int | None = None # if time, expressed in days, in 'count' in number of work orders
  kpi_window_type: Optional[KPIWindowType] = KPIWindowType.COUNT

  metadata: List[ProductMetadataField] | None = None

class ProductDoc(FlexModel):
  name: str
  size: ByteSize

class ProductFull(ProductDetails):
  docs: List[ProductDoc] = []
  img_name: str | None = None
  counter: Counter | None = None


class ProductSearchParams(BaseModel):
  search_string: str | None = None
  search_description: bool = False
  tag_key: str | None = None
  include_text: str | None = None
  exclude_text: str | None = None
  include_tags: list[str] | None = None
  exclude_tags: list[str] | None = None
  include_tags_operator: Literal["ALL", "ANY"] = "ALL"
  exclude_tags_operator: Literal["ALL", "ANY"] = "ANY"
  has_operation_key: str | None = None
  active_only: bool = True
  traceability_only: bool = False
  details: bool = False
  limit: None | int = None
  offset: int = 0

  @field_validator('search_string', 'include_text', 'exclude_text', mode='after')
  def convert_wildcard_to_regex(cls, v):
    return wildcard_to_regex(v)
