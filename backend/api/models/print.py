from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field

from utils.base_models import ArangoDocument, ArangoEdge

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
  DATAMATRIX = 'gs1datamatrix'
  JAPANPOST = 'japanpost'
  NW7 = 'nw7'
  ITF14 = 'itf14'
  UPCA = 'upca'
  UPCE = 'upce'


class DynamicFontSize(BaseModel):
  fit: str | None = None
  max: float | None = None
  min: float | None = None

class Position(BaseModel):
  x: float
  y: float


# Due to javascript library specs, properties must be specified in camelCase

class TextFieldSpec(BaseModel):
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

class VisualFieldSpec(BaseModel):
  """Image or linear/2D codes"""
  type: VisualFieldType
  position: Position
  height: float
  rotate: float | None = None
  width: float

FieldSpec = TextFieldSpec | VisualFieldSpec
PageSchema = dict[str, FieldSpec] # field name -> field details

class PrintTemplate(BaseModel):
  basePdf: str | None = None
  columns: list[str] = []
  sampledata: list[dict[str, str]] = []
  schemas: list[PageSchema]

class PrintTemplateLinkType(str, Enum):
  PRESET = 'preset'
  CUSTOM_FIELD = 'custom_field'

class PrintTemplateLink(BaseModel):
  type: PrintTemplateLinkType
  value: str | None = None

class PrintTemplateRecord(ArangoDocument):
  name: str
  description: str | None = None
  links: dict[str, PrintTemplateLink] = dict()
  template: PrintTemplate | None = None


class TemplateAssignment(ArangoEdge):
  type: str = 'TemplateAssignment'

class TemplateAssignmentContext(str, Enum):
  PRODUCT = 'product'
  PHASE = 'phase'
  STEP = 'step'
  ISSUE_TYPE = 'issue_type'

class TemplateAssignmentUpdateType(str, Enum):
  ADD = 'add'
  REMOVE = 'remove'

class TemplateAssignmentUpdate(BaseModel):
  type: TemplateAssignmentUpdateType
  template_key: str
  context: TemplateAssignmentContext
  context_key: str
