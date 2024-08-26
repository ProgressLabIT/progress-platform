from datetime import datetime
from enum import Enum
from random import randrange, uniform
from typing import List, Optional

from pydantic import ByteSize, Field

from commons.models.base_models import FlexModel
from commons.models.tag import Tag
from commons.models.counter import Counter



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
  active: bool = True
  image: bool = False # to be replaced with Object Storage url in the future
  tags: List[Tag] | None= []
  counter_key: str | None = None
  traceability_level: TraceabilityLevel | None = None

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

class ProductDoc(FlexModel):
  name: str
  size: ByteSize

class ProductFull(ProductDetails):
  docs: List[ProductDoc] = []
  img_name: str | None = None
  counter: Counter | None = None
