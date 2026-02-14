from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field

from models.base_models import ArangoDocument, ArangoEdge

class Alignment(str, Enum):
  CENTER = 'center'
  LEFT = 'left'
  RIGHT = 'right'

class VerticalAlignment(str, Enum):
  TOP = 'top'
  MIDDLE = 'middle'
  BOTTOM = 'bottom'

class VisualFieldType(str, Enum):
  IMAGE = 'image'
  QRCODE = 'qrcode'
  EAN13 = 'ean13'
  CODE39 = 'code39'
  CODE128 = 'code128'
  DATAMATRIX = 'gs1datamatrix'
  JAPANPOST = 'japanpost'
  NW7 = 'nw7'
  ITF14 = 'itf14'
  UPCA = 'upca'
  UPCE = 'upce'

class LinkType(str, Enum):
  NONE = 'none'
  PRESET = 'preset'
  CUSTOM_FIELD = 'custom_field'


class DynamicFontSize(BaseModel):
  fit: str | None = None
  max: float | None = None
  min: float | None = None

class Position(BaseModel):
  x: float
  y: float


# Due to javascript library specs, properties must be specified in camelCase
# pdfme v5: each field carries its own name and optional link configuration

class TextFieldSpec(BaseModel):
  name: str
  type: Literal['text'] = 'text'
  position: Position
  height: float
  width: float

  alignment: Alignment | None = None
  backgroundColor: str | None = None
  characterSpacing: float | None = None
  dynamicFontSize: DynamicFontSize | None = None
  fontColor: str | None = None
  fontName: str | None = None
  fontSize: float | None = None
  lineHeight: float | None = None
  rotate: float | None = None
  verticalAlignment: VerticalAlignment | None = None

  # Link configuration
  linkType: LinkType | None = None
  linkValue: str | None = None
  customFieldKey: str | None = None
  extraPath: str | None = None

  # pdfme v5 form behavior
  readOnly: bool | None = None
  required: bool | None = None

class VisualFieldSpec(BaseModel):
  """Image or linear/2D codes"""
  name: str
  type: VisualFieldType
  position: Position
  height: float
  width: float
  rotate: float | None = None

  # Link configuration
  linkType: LinkType | None = None
  linkValue: str | None = None
  customFieldKey: str | None = None
  extraPath: str | None = None

  # pdfme v5 form behavior
  readOnly: bool | None = None
  required: bool | None = None

FieldSpec = TextFieldSpec | VisualFieldSpec
PageSchema = list[FieldSpec] # v5: array of field specs, each with a name property

class PrintTemplate(BaseModel):
  basePdf: str | None = None
  sampledata: list[dict[str, str]] = []
  schemas: list[PageSchema]
  pdfmeVersion: str | None = None

class PrintTemplateRecord(ArangoDocument):
  name: str
  description: str | None = None
  template: PrintTemplate | None = None
  entities: int | None = 0


class TemplateAssignment(ArangoEdge):
  type: str = 'TemplateAssignment'

class TemplateAssignmentContext(str, Enum):
  PRODUCT = 'product'
  PHASE = 'phase'
  STEP = 'step'
  ISSUE_TYPE = 'issue_type'
  TASK_TYPE = 'task_type'
  TEMPLATE = 'template'
  POSITION = 'position'

class TemplateAssignmentUpdateType(str, Enum):
  ADD = 'add'
  REMOVE = 'remove'

class TemplateAssignmentUpdate(BaseModel):
  type: TemplateAssignmentUpdateType
  template_key: str
  context: TemplateAssignmentContext
  context_key: str
