from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict, Field

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
  GS1DATAMATRIX = 'gs1datamatrix'
  DATAMATRIX = 'datamatrix'
  JAPANPOST = 'japanpost'
  NW7 = 'nw7'
  ITF14 = 'itf14'
  UPCA = 'upca'
  UPCE = 'upce'

class LinkType(str, Enum):
  NONE = 'none'
  PRESET = 'preset'
  CUSTOM_FIELD = 'custom_field'
  TEMPLATE_EXPRESSION = 'template_expression'
  COMPUTED = 'computed'


class DynamicFontSize(BaseModel):
  fit: str | None = Field(None, description="Fit mode for dynamic font sizing (e.g. 'shrink').", examples=["shrink"])
  max: float | None = Field(None, description="Maximum font size in points.", examples=[12.0])
  min: float | None = Field(None, description="Minimum font size in points.", examples=[6.0])

class Position(BaseModel):
  x: float = Field(..., description="Horizontal position of the field in millimetres from the left edge.", examples=[10.0])
  y: float = Field(..., description="Vertical position of the field in millimetres from the top edge.", examples=[20.0])


# Due to javascript library specs, properties must be specified in camelCase
# pdfme v5: each field carries its own name and optional link configuration

class TextFieldSpec(BaseModel):
  model_config = ConfigDict(extra='allow')

  name: str = Field(..., description="Unique field name within the page schema, used to bind data values.", examples=["serial_number"])
  type: Literal['text'] = Field('text', description="pdfme field type discriminator; always 'text' for text fields.", examples=["text"])
  position: Position = Field(..., description="Position of the text field on the page in millimetres.")
  height: float = Field(..., description="Height of the text field in millimetres.", examples=[8.0])
  width: float = Field(..., description="Width of the text field in millimetres.", examples=[60.0])

  alignment: Alignment | None = Field(None, description="Horizontal text alignment within the field.", examples=["left"])
  backgroundColor: str | None = Field(None, description="Background colour as a CSS hex string.", examples=["#ffffff"])
  characterSpacing: float | None = Field(None, description="Letter spacing in points.", examples=[0.0])
  dynamicFontSize: DynamicFontSize | None = Field(None, description="Dynamic font size configuration; null uses a fixed fontSize.")
  fontColor: str | None = Field(None, description="Font colour as a CSS hex string.", examples=["#000000"])
  fontName: str | None = Field(None, description="Font name registered with pdfme.", examples=["NotoSerifJP-Regular"])
  fontSize: float | None = Field(None, description="Fixed font size in points.", examples=[10.0])
  lineHeight: float | None = Field(None, description="Line height multiplier.", examples=[1.0])
  rotate: float | None = Field(None, description="Rotation angle in degrees.", examples=[0.0])
  verticalAlignment: VerticalAlignment | None = Field(None, description="Vertical text alignment within the field.", examples=["top"])

  # Link configuration
  linkType: LinkType | None = Field(None, description="How this field's value is bound at render time.", examples=["preset"])
  linkValue: str | None = Field(None, description="Preset key or expression used when linkType is 'preset' or 'template_expression'.", examples=["serial_number"])
  customFieldKey: str | None = Field(None, description="ArangoDB _key of the CustomField used when linkType='custom_field'.", examples=["cf-001"])
  extraPath: str | None = Field(None, description="JSONPath expression for extracting a nested value from the linked data source.", examples=["batch.code"])
  templateExpression: str | None = Field(None, description="Jinja-style expression evaluated against render context when linkType='template_expression'.", examples=["{{ serial.code }}"])

  # pdfme v5 form behavior
  readOnly: bool | None = Field(None, description="When true, the field is read-only in pdfme form mode.", examples=[True])
  required: bool | None = Field(None, description="When true, the field is required in pdfme form mode.", examples=[False])

class VisualFieldSpec(BaseModel):
  """Image or linear/2D codes"""
  model_config = ConfigDict(extra='allow')

  name: str = Field(..., description="Unique field name within the page schema.", examples=["product_qr"])
  type: VisualFieldType = Field(..., description="pdfme visual field type: 'image', 'qrcode', 'ean13', 'code128', etc.", examples=["qrcode"])
  position: Position = Field(..., description="Position of the visual field on the page in millimetres.")
  height: float = Field(..., description="Height of the visual field in millimetres.", examples=[20.0])
  width: float = Field(..., description="Width of the visual field in millimetres.", examples=[20.0])
  rotate: float | None = Field(None, description="Rotation angle in degrees.", examples=[0.0])

  # Link configuration
  linkType: LinkType | None = Field(None, description="How this field's value is bound at render time.", examples=["preset"])
  linkValue: str | None = Field(None, description="Preset key or expression for the linked value.", examples=["serial_number"])
  customFieldKey: str | None = Field(None, description="ArangoDB _key of the CustomField used when linkType='custom_field'.", examples=["cf-001"])
  extraPath: str | None = Field(None, description="JSONPath expression for extracting a nested value.", examples=["batch.code"])
  templateExpression: str | None = Field(None, description="Jinja-style expression evaluated against render context.", examples=["{{ serial.code }}"])

  # pdfme v5 form behavior
  readOnly: bool | None = Field(None, description="When true, the field is read-only in pdfme form mode.", examples=[True])
  required: bool | None = Field(None, description="When true, the field is required in pdfme form mode.", examples=[False])

FieldSpec = TextFieldSpec | VisualFieldSpec
PageSchema = list[FieldSpec] # v5: array of field specs, each with a name property

class BlankPdf(BaseModel):
  """pdfme BlankPdf format — blank page with explicit dimensions in mm."""
  width: float = Field(..., description="Page width in millimetres.", examples=[210.0])
  height: float = Field(..., description="Page height in millimetres.", examples=[297.0])
  padding: list[float] = Field([0, 0, 0, 0], description="Page padding [top, right, bottom, left] in millimetres.", examples=[[0, 0, 0, 0]])

class PrintTemplate(BaseModel):
  basePdf: str | BlankPdf | None = Field(None, description="Base PDF as a base64-encoded string, or a BlankPdf dimension spec for blank-page templates.", examples=[None])
  sampledata: list[dict[str, str]] = Field([], description="Sample data rows used in the template editor preview; each dict maps field names to example strings.", examples=[[]])
  schemas: list[PageSchema] = Field(..., description="Ordered list of page schemas; each page schema is an array of FieldSpec objects defining the template layout.", examples=[[]])
  pdfmeVersion: str | None = Field(None, description="pdfme library version string that generated this template.", examples=["5.5.0"])

class PrintTemplateRecord(ArangoDocument):
  name: str = Field(..., description="Human-readable name for this print template.", examples=["Serial Label A6"])
  description: str | None = Field(None, description="Optional description of the template's purpose and usage context.", examples=["A6 label for finished goods with QR code and serial number"])
  template: PrintTemplate | None = Field(None, description="Full pdfme template definition; null in list responses, populated in detail responses.")
  entities: int | None = Field(0, description="Number of entities (products, phases, steps, etc.) this template is assigned to via can_use_print_template edges.", examples=[3])


class TemplateAssignment(ArangoEdge):
  type: str = Field('TemplateAssignment', description="Edge type identifier in the graph.", examples=["TemplateAssignment"])

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
  type: TemplateAssignmentUpdateType = Field(..., description="Whether to add or remove this template assignment.", examples=["add"])
  template_key: str = Field(..., description="ArangoDB _key of the PrintTemplate to assign or unassign.", examples=["tmpl-001"])
  context: TemplateAssignmentContext = Field(..., description="Entity type this assignment links to.", examples=["product"])
  context_key: str = Field(..., description="ArangoDB _key of the entity (product, phase, step, etc.) being linked.", examples=["prod-001"])
