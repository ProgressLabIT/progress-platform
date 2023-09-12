from enum import Enum
from typing import Union

from pydantic import BaseModel, Field

from utils.base_models import ArangoDocument


class Alignment(Enum):
  CENTER = 'center'
  LEFT = 'left'
  RIGHT = 'right'

class VerticalAlignment(Enum):
  TOP = 'top'
  MIDDLE = 'middle'
  BOTTOM = 'bottom'

class VisualFieldType(Enum):
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
  type: VisualFieldTypes
  position: Position
  height: float
  rotate: float = None
  width: float

FieldSpec = Union[TextFieldSpec, VisualFieldSpec]
PageSchema = dict[str, FieldSpec] # field name -> field details

class PrintTemplate(ArangoDocument):
  basePdf: str = None
  schemas: list[PageSchema] = Field([], union_mode='left_to_right')


