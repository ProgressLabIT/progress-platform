from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from commons.models.base_models import FlexModel, ArangoEdge, ArangoDocument
from commons.models.form import FormFieldValue

class StepData(BaseModel):
  step_key: str | None = None
  title: str | None = None
  data: list[FormFieldValue] | None = None

class PhaseData(BaseModel):
  phase_hey: str | None = None
  alias: str | None = None
  steps: list[StepData] | None = None

class Serial(ArangoDocument):
   serial: str | None = None
   created_by: str | None = None
   #product_key: str
   #wo_key: str
   created: datetime | None = None
   released: datetime | None = None
   #locations: list[str]
   #status: str
   data: list[FormFieldValue] | None = None
   phases: list[PhaseData] | None = None

class SerialLinkType(str, Enum):
  PRODUCT = 'product'
  USER = 'user'
  COUNTER = 'counter'

class SerialLink(BaseModel):
  type: SerialLinkType
  key: str

class SerialWithLinks(Serial):
  linked_to: list[SerialLink] = []
