from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from commons.models.base_models import ArangoDocument

class Serial(ArangoDocument):
   serial: str | None = None
   #product_key: str
   #wo_key: str
   created: datetime | None = None
   released: datetime | None = None
   #locations: list[str]
   #status: str

class SerialLinkType(str, Enum):
  PRODUCT = 'product'
  USER = 'user'
  JOB = 'job'

class SerialLink(BaseModel):
  type: SerialLinkType
  key: str

class SerialWithLinks(Serial):
  linked_to: list[SerialLink] = []
