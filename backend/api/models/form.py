from enum import Enum
from datetime import date, time
from typing import Any, List, Union

from pydantic import BaseModel, root_validator

from utils.base_models import ArangoDocument



class FileBucket(Enum):
  ISSUE = 'issue'
  PRODUCT = 'product'
  STEP = 'step'
  USER = 'user'

class FileTargetData(BaseModel):
  bucket: FileBucket
  key: str


class FieldType(Enum):
  TEXT = 'text'
  NUMBER = 'number'
  BOOLEAN = 'boolean'
  # TERNARY = 'ternary'
  CHOICE = 'choice'
  DATE = 'date'
  TIME = 'time'
  ATTACHMENT = 'attachment'
  # Files will added to the form through a boolean parameter in the endpoint
  # No need to specify a field of type "file"
  # In the future these will be saved as in a Media collection with metadata
  # and pointing to an object storage location

field_type_map = {
  FieldType.TEXT.value: str,
  FieldType.NUMBER.value: float,
  FieldType.BOOLEAN.value: bool,
  # FieldType.TERNARY.value: Union[bool, None],
  FieldType.CHOICE.value: str,
  FieldType.DATE.value: date,
  FieldType.TIME.value: time,
  FieldType.ATTACHMENT.value: bytes
}
# if the field model has multiple = True, the type becomes List[type]


class CustomListValue(BaseModel):
  field_key: str # Reference to CustomField
  ext_key: str = None # Optional reference to external identification, e.g. ERP id
  value: str


class CustomField(ArangoDocument):
  type: FieldType
  use_dropdown: bool = None # Only relevant for choice fields
  name: str # To search when building the form
  default_label: str = None # To show to the user when filling up the forms
  default_hint: str = None # To show to the user when filling up the forms

  @root_validator
  def ensure_type_if_choice(cls, values):
    if values.get('type') == FieldType.CHOICE and values.get('use_dropdown') == None:
      values['use_dropdown'] = True
    return values

class CustomFieldInstance(BaseModel):
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
