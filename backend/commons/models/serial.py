from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from commons.models.base_models import FlexModel, ArangoEdge, ArangoDocument
from commons.models.form import SerialFormFieldValue

#class StepData(BaseModel):
#  step_key: str | None = None
#  title: str | None = None
#  data: list[FormFieldValue] | None = None#

#class PhaseData(BaseModel):
#  phase_key: str | None = None
#  alias: str | None = None
#  steps: list[StepData] | None = None

class Serial(ArangoDocument):
   serial: str | None = None
   created_by: str | None = None
   operation: str | None = None
   product_key: str | None = None
   wo_key: str | None = None
   counter_key: str | None = None
   user_key: str | None = None
   created: datetime | None = None
   released: datetime | None = None
   data: list[SerialFormFieldValue] | None = None
   deleted: bool = False
