from datetime import date, time, datetime
from typing import Any, Union

from pydantic import BaseModel, Field, model_validator

from commons.models.base_models import ArangoDocument
from commons.utils.dt import timestamp

class Counter(ArangoDocument):
  name: str = Field(..., min_length=1)
  next_tick: int = 0
  template: list[str] = []
  frequency: str | None = None
  reset_date: datetime = Field(default_factory=timestamp)

