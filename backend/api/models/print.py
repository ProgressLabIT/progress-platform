from enum import Enum
from typing import Union

from pydantic import BaseModel, Field

from models.form import FormFieldInstance
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
  fit: str = None
  max: float = None
  min: float = None

class Position(BaseModel):
  x: float
  y: float


# Due to javascript library specs, properties must be specified in camelCase

class TextFieldSpec(BaseModel):
  type: str = Field('text', const=True)
  position: Position
  height: float
  width: float

  alignment: Alignment = None
  backgroundColor: str = None
  characterSpacing: float = None
  dynamicFontSize: DynamicFontSize = None
  fontColor: str = None
  fontName: str = None
  fontSize: float = None
  lineHeight: float = None
  rotate: float = None
  verticalAlignment: VerticalAlignment = None

class VisualFieldSpec(BaseModel):
  """Image or linear/2D codes"""
  type: VisualFieldType
  position: Position
  height: float
  rotate: float = None
  width: float

FieldSpec = Union[TextFieldSpec, VisualFieldSpec]
PageSchema = dict[str, FieldSpec] # field name -> field details

class PrintTemplate(BaseModel):
  basePdf: str = None
  columns: list[str] = []
  sampledata: list[dict[str, str]] = []
  schemas: list[PageSchema] = Field(..., union_mode='left_to_right')

class PrintTemplateLinkType(str, Enum):
  PRESET = 'preset'
  CUSTOM_FIELD = 'custom_field'

class PrintTemplateLink(BaseModel):
  type: PrintTemplateLinkType
  value: str = None

class PrintTemplateRecord(ArangoDocument):
  name: str
  description: str = None
  links: dict[str, PrintTemplateLink] = dict()
  template: PrintTemplate = None


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
