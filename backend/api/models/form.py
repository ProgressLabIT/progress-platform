from enum import Enum
from datetime import date, time
from typing import Any, List, Union

from pydantic import BaseModel, Field, root_validator

from utils.base_models import ArangoDocument


class FileBucket(str, Enum):
  ISSUE = 'issue'
  PRODUCT = 'product'
  STEP = 'step'
  USER = 'user'

class FileTargetData(BaseModel):
  bucket: FileBucket
  object_key: str
  subfolder: str = None

class FieldType(str, Enum):
  TEXT = 'text'
  NUMBER = 'number'
  BOOLEAN = 'boolean'
  # TERNARY = 'ternary'
  CHOICE = 'choice'
  DATE = 'date'
  TIME = 'time'
  FILES = 'files'

field_type_map = {
  FieldType.TEXT.value: str,
  FieldType.NUMBER.value: float,
  FieldType.BOOLEAN.value: bool,
  # FieldType.TERNARY.value: Union[bool, None],
  FieldType.CHOICE.value: str,
  FieldType.DATE.value: date,
  FieldType.TIME.value: time,
  FieldType.FILES.value: bytes
}
# if the field model has multiple = True, the type becomes List[type]

class CustomListValue(ArangoDocument):
  field_key: str # Reference to CustomField
  ext_key: str = None # Optional reference to external identification, e.g. ERP id
  value: str

class CustomField(ArangoDocument):
  type: FieldType
  name: str = Field(..., min_length=1) # To search when building the form
  default_label: str = None # To show to the user when filling up the forms
  default_hint: str = None # To show to the user when filling up the forms

class FormFieldDefinition(BaseModel):
  field_key: str
  multiple: bool = False
  label: str
  hint: str = None
  default: str = None # this value should be able to be parsed to get current data
  required: bool = False
  hidden: bool = None

  @root_validator(pre=True)
  def ensure_default_for_hidden(cls, values):
    if values.get('hidden') and values.get('default') == None:
      raise ValueError('Hidden fields must have a default value')
    return values
