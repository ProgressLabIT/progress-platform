from datetime import date, time, datetime
from typing import Any, Union

from pydantic import BaseModel, Field, model_validator

from utils.base_models import ArangoDocument
from utils.dt import timestamp

class Counter(ArangoDocument):
  name: str = Field(..., min_length=1)
  next_tick: int = 0
  template: list[str] = []
  frequency: str | None = None
  reset_date: datetime = Field(default_factory=timestamp)


### PD ????
class CounterDefinition(BaseModel):
  key: str | None = Field(None, alias="_key")
  custom_field_key: str
  multiple: bool = False
  label: str | None = None
  hint: str | None = None
  default: str | None = None # this value should be able to be parsed to get current data
  required: bool = False
  hidden: bool | None = None

  @model_validator(mode="before")
  @classmethod
  def ensure_default_for_hidden(cls, values):
    if values.get('hidden') and values.get('default') == None:
      raise ValueError('Hidden fields must have a default value')
    return values
