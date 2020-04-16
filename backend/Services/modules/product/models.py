from random import randrange, uniform
from typing import List, Optional

from pydantic import ByteSize, Field

from utils.base_models import FlexModel



class TargetAverageCost(FlexModel):
  target: float = randrange(500, 120000, 100)
  average: float = target * (1 + uniform(-0.2, 0.2))


class TargetAverageTime(TargetAverageCost):
  target: float = randrange(900000, 216000000, 705267)
  average: float = target * (1 + uniform(-0.2, 0.2))


class ProductData(FlexModel):
  key: str = Field(None, alias="_key")
  code: str
  description: Optional[str] = None
  active: bool = True
  trash: bool = False
  cost: TargetAverageCost = TargetAverageCost()
  # sale_price: float = 0
  # margin: TargetAverageData = TargetAverageData()
  technical_batch_qt: int = 0
  # economic_order_qt: int = 0   ----> Doesn't make sense in a MTO/ATO context: only for purchases or MTS
  minimum_order_qt: int = 0
  # tags: List[str] = []
  process_phases: List[str] = [] 
  lead_time: TargetAverageTime = TargetAverageTime()
  throughput_time: TargetAverageTime = TargetAverageTime()
  processing_time: TargetAverageTime = TargetAverageTime()

class ProductDoc(FlexModel):
  name: str
  size: ByteSize

class ProductFull(ProductData):
  docs: List[ProductDoc] = []
  img_name: str = None