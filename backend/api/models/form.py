from enum import Enum
from datetime import date, time
from typing import Any, Union

from pydantic import BaseModel, Field, model_validator

from models.base_models import ArangoDocument


class FileBucket(str, Enum):
  ISSUE = 'issue'
  PRODUCT = 'product'
  STEP = 'step'
  TRACEABILITY = 'traceability'
  USER = 'user'
  SERIAL = 'serial'
  TASK = 'task'

class FileTargetData(BaseModel):
  bucket: FileBucket = Field(..., description="Storage bucket category for the file.", examples=["step"])
  object_key: str = Field(..., description="ArangoDB _key of the entity this file belongs to.", examples=["step-001"])
  subfolder: str | None = Field(None, description="Optional subfolder within the bucket for organising files.", examples=["attachments"])

class FieldType(str, Enum):
  TEXT = 'text'
  NUMBER = 'number'
  BOOLEAN = 'boolean'
  TERNARY = 'ternary'
  CHOICE = 'choice'
  DATE = 'date'
  TIME = 'time'
  FILES = 'files'
  SEPARATOR = 'separator'

field_type_map = {
  FieldType.TEXT.value: str,
  FieldType.NUMBER.value: float,
  FieldType.BOOLEAN.value: bool,
  FieldType.TERNARY.value: Union[bool, None],
  FieldType.CHOICE.value: str,
  FieldType.DATE.value: date,
  FieldType.TIME.value: time,
  FieldType.FILES.value: bytes
}
# if the field model has multiple = True, the type becomes List[type]

class CustomListValue(ArangoDocument):
  field_key: str = Field(..., description="ArangoDB _key of the CustomField this list value belongs to.", examples=["cf-001"])
  ext_key: str | None = Field(None, description="Optional external identifier (e.g. ERP code) for this list value.", examples=["ERP-COL-9005"])
  value: str = Field(..., description="Display value shown to the operator when filling the form.", examples=["RAL 9005 Jet Black"])

class CustomField(ArangoDocument):
  type: FieldType = Field(..., description="Data type of this custom field, determining how it is rendered and validated.", examples=["text"])
  name: str = Field(..., min_length=1, description="Unique human-readable name used to identify this field and compute its slug.", examples=["Surface Colour"])
  default_label: str | None = Field(None, description="Default label shown to the operator when filling a form; can be overridden per-instance.", examples=["Surface Colour"])
  default_hint: str | None = Field(None, description="Default hint text shown below the field input; can be overridden per-instance.", examples=["Select the RAL colour code applied to this part"])

class FormFieldDefinition(BaseModel):
  key: str | None = Field(None, alias="_key", description="ArangoDB _key of this form field definition instance.", examples=["ffd-001"])
  custom_field_key: str = Field(..., description="ArangoDB _key of the CustomField definition this instance is linked to.", examples=["cf-001"])
  multiple: bool = Field(False, description="When true, the operator can select or enter multiple values for this field.", examples=[False])
  label: str | None = Field(None, description="Label override for this form field instance; falls back to CustomField.default_label.", examples=["Colour Code"])
  hint: str | None = Field(None, description="Hint text override for this instance; falls back to CustomField.default_hint.", examples=["Verify against approved colour chart"])
  default: str | None = Field(None, description="Default value pre-populated in the field; must be parseable to the field type. Required when hidden=true.", examples=["pass"])
  mandatory: bool = Field(False, description="When true, the operator must fill this field before completing the step.", examples=[False])
  hidden: bool | None = Field(None, description="When true, the field is hidden from the operator and filled automatically from default.", examples=[False])

  @model_validator(mode="before")
  @classmethod
  def ensure_default_for_hidden(cls, values):
    if values.get('hidden') and values.get('default') == None:
      raise ValueError('Hidden fields must have a default value')
    return values

class FormFieldValue(BaseModel):
  form_field_key: str = Field(..., description="ArangoDB _key of the FormFieldDefinition this value corresponds to.", examples=["ffd-001"])
  # This causes data duplication, but it's for ease of access.
  # It can't be changed in FormField, so there is no risk of data inconsistency, at least for now.
  custom_field_key: str | None = Field(None, description="ArangoDB _key of the CustomField definition; duplicated from FormFieldDefinition for read performance.", examples=["cf-001"])
  value: Any | None = Field(None, description="Recorded value for this field instance; type depends on the associated FieldType.", examples=["RAL 9005"])


class TaskFormFieldValue(BaseModel):
  form_field_key: str = Field(..., description="ArangoDB _key of the FormFieldDefinition.", examples=["ffd-001"])
  custom_field_key: str = Field(..., description="ArangoDB _key of the associated CustomField.", examples=["cf-001"])
  label: str = Field(..., description="Resolved label for display in the task UI.", examples=["Surface Colour"])
  hint: str | None = Field(None, description="Resolved hint text for display in the task UI.", examples=["Verify against approved colour chart"])
  mandatory: bool | None = Field(False, description="Whether this field must be completed before the task can close.", examples=[False])
  value: Any | None = Field(None, description="Current recorded value for this field on this task.", examples=[None])
  last_updated: str | None = Field(None, description="ISO 8601 timestamp of the last time this field value was updated.", examples=["2026-03-22T14:30:00Z"])


class SerialFormFieldValue(BaseModel):
  form_field_key: str | None = Field(None, description="ArangoDB _key of the FormFieldDefinition.", examples=["ffd-001"])
  custom_field_key: str | None = Field(None, description="ArangoDB _key of the associated CustomField.", examples=["cf-001"])
  label: str | None = Field(None, description="Resolved label for traceability display.", examples=["Surface Colour"])
  hint: str | None = Field(None, description="Resolved hint text.", examples=["Verify against approved colour chart"])
  mandatory: bool | None = Field(None, description="Whether this field was mandatory at the time of recording.", examples=[False])
  value: Any | None = Field(None, description="Recorded value for the serial traceability record.", examples=["RAL 9005"])
  batch_key: str | None = Field(None, description="ArangoDB _key of the production batch during which this value was recorded.", examples=["batch-001"])
  step_key: str | None = Field(None, description="ArangoDB _key of the step at which this value was recorded.", examples=["step-001"])
  phase_key: str | None = Field(None, description="ArangoDB _key of the phase at which this value was recorded.", examples=["phase-001"])
  last_updated: str | None = Field(None, description="ISO 8601 timestamp of the last time this field value was updated.", examples=["2026-03-22T14:30:00Z"])
