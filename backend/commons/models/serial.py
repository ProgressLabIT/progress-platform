from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from commons.models.base_models import FlexModel, ArangoEdge, ArangoDocument
from commons.models.form import SerialFormFieldValue

class Serial(ArangoDocument):
   serial: str | None = None
   created_by: str | None = None
   product_key: str | None = None
   wo_key: str | None = None
   counter_key: str | None = None
   user_key: str | None = None
   quantity: int = 1
   created: datetime | None = None
   released: datetime | None = None
   data: list[SerialFormFieldValue] | None = None
   deleted: bool = False

class SerialEvent(Serial):
   operation: str | None = None
   batch_key: str | None = None
   serial: Serial | None = None
