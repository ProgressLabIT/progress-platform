from datetime import datetime
from enum import Enum
from random import randrange, uniform
from typing import Any

from pydantic import BaseModel, ByteSize, Field, model_validator

from models.base_models import FlexModel
from models.process import ProcessTaskDefinition
from models.tag import Tag
from models.counter import Counter



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
  tags: list[Tag] | None= []
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
  process_phases: list[str] = []
  process_tasks: list[ProcessTaskDefinition] = [] # list of task type keys
  production_notes: str | None = None

  throughput_time_target: float | None = None #TargetAverageTime = TargetAverageTime()
  processing_time_target: float | None = None #TargetAverageTime = TargetAverageTime()

  kpi_window_size: int | None = None # if time, expressed in days, in 'count' in number of work orders
  kpi_window_type: KPIWindowType | None = KPIWindowType.COUNT

  metadata: list[ProductMetadataField] | None = None


  @model_validator(mode='after')
  def validate_process_tasks(self):
    """Validate that process tasks reference valid phases and define valid intervals"""
    if not self.process_tasks:
      return self

    process = self.process_phases
    valid_phase_keys = set(process)

    for task in self.process_tasks:
      if task.before_phase and task.before_phase not in valid_phase_keys:
        raise ValueError(f"Phase {task.before_phase} not found in product process")
      if task.after_phase and task.after_phase not in valid_phase_keys:
        raise ValueError(f"Phase {task.after_phase} not found in product process")

      # Ensure after_phase and before_phase define a valid interval in the production process
      # such as task should be executed in the range (after_phase, before_phase)
      # phases are not included in the range
      if task.before_phase is not None and task.after_phase is not None:
        # We already checked that after_phase and before_phase are in the process
        after_index = process.index(task.after_phase)
        before_index = process.index(task.before_phase)
        if before_index <= after_index:
          raise ValueError("Before and after phase must define a valid interval for the execution of the task. You have provided an invalid interval where before_phase is before after_phase.")
    return self

class ProductDoc(FlexModel):
  name: str
  size: ByteSize

class ProductFull(ProductDetails):
  docs: list[ProductDoc] = []
  img_name: str | None = None
  counter: Counter | None = None
