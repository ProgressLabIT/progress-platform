from datetime import date, datetime
from enum import Enum
from typing import Any
from typing import Annotated


from pydantic import BaseModel, ConfigDict, Field, model_validator, StringConstraints, field_serializer, field_validator

from models.base_models import ArangoDocument, FlexModel
#from utils.counter import _generate_counter
from utils.dt import timestamp
from utils.search import WildcardString
from utils.float_precision import round_float



# ========================================================
# MOVEMENTS
# ========================================================

class MovementStatus(str, Enum):
  PLANNED = 'planned'
  STARTED = 'started'
  COMPLETED = 'completed'
  CANCELED = 'canceled'


class InventoryMovementType(str, Enum):
  TRANSFER = 'transfer'
  RECEIPT = 'receipt'
  SHIPMENT = 'shipment'
  PRODUCTION = 'production'
  CONSUMPTION = 'consumption'
  ADJUSTMENT = 'adjustment'
  REVERSAL = 'reversal'

class InventoryMovementReferences(BaseModel):
  work_order_key: str | None = None
  job_key: str | None = None
  batch_key: str | None = None
  origin_movement_key: str | None = None
  transfer_doc: str | None = None
  sales_doc: str | None = None
  purchase_doc: str | None = None
  partner_name: str | None = None # supplier/customer name
  partner_code: str | None = None # supplier/customer code
  inventory_count_session_key: str | None = None


class InventoryMovementNew(FlexModel):
  model_config = ConfigDict(populate_by_name=True)

  position_from: str | None = Field(None, serialization_alias='_from')
  position_to: str | None = Field(None, serialization_alias='_to')
  movement_type: InventoryMovementType = Field(..., serialization_alias='type')
  status: MovementStatus | None = MovementStatus.COMPLETED
  product_key: str | None = None
  product_code: str | None = None
  serial_key: str | None = None
  serial_code: str | None = None
  qt_planned: float | None = 1
  qt_confirmed: float | None = 0
  created: datetime | None = Field(default_factory=timestamp)
  start: datetime | None = None
  end: datetime | None = None
  movement_list_key: str | None = None # link to MovementList document, if present
  movement_list_item: float | None = None # "row" number in the movement list
  references: InventoryMovementReferences | None = None
  reason: str | None = None
  user_key: str | None = None
  extra: Any = None

  @field_validator('qt_planned', 'qt_confirmed', mode='before')
  @classmethod
  def round_float_fields(cls, v):
    """Round float fields to prevent floating-point precision noise."""
    if isinstance(v, float):
      return round_float(v)
    return v

  @model_validator(mode='before')
  def set_implicit_values(cls, values):
    match values.get('movement_type', None):
      case InventoryMovementType.PRODUCTION.value:
        values['position_from'] = 'NULL'
        values['position_to'] = values.get('position_to', 'IN')
      case InventoryMovementType.CONSUMPTION.value:
        values['position_to'] = 'NULL'
        values['position_from'] = values.get('position_from', 'IN')
      case InventoryMovementType.SHIPMENT.value:
        values['position_to'] = 'OUT'
        values['position_from'] = values.get('position_from', 'IN')
      case InventoryMovementType.RECEIPT.value:
        values['position_from'] = 'OUT'
        values['position_to'] = values.get('position_to', 'IN')
      case _:
        pass

    if values.get('status') in [MovementStatus.STARTED.value, MovementStatus.COMPLETED.value] and values.get('start', None) is None:
      values['start'] = timestamp()
    if values.get('status') == MovementStatus.COMPLETED.value and values.get('end', None) is None:
      values['end'] = timestamp()
    return values

  @model_validator(mode='after')
  def validate(self):
    # Ensure a movement has a product reference or container position
    if self.product_key is None and self.product_code is None:
      if not(self.movement_type == InventoryMovementType.TRANSFER and self.position_from is not None):
        raise ValueError("A new movement must include a product or container position")

    # Ensure a confirmed serial movement has a quantity of +/-1
    if self.serial_key is not None and self.status == MovementStatus.COMPLETED and (abs(self.qt_planned) > 1 or abs(self.qt_confirmed) > 1):
      raise ValueError("A serial movement must have a quantity of +/-1")

    # Ensure every non-adjustment movement has a different position from and to
    if self.position_from == self.position_to and self.movement_type not in [InventoryMovementType.ADJUSTMENT, InventoryMovementType.REVERSAL]:
      raise ValueError("A movement must have a different position from and to")
    return self

  @field_serializer('position_from')
  def serialize_position_from(self, position_from, _info):
    return position_from if position_from.startswith('Position/') else f'Position/{position_from}'

  @field_serializer('position_to')
  def serialize_position_to(self, position_to, _info):
    return position_to if position_to.startswith('Position/') else f'Position/{position_to}'


class InventoryMovement(ArangoDocument): # edge collection movement
  # can be a segment of a multistep movement (to be used as graph),
  # in case material needs to be assigned a specific position in e.g. a transfer trolley with codified shelves
  # or in the future via a specific transport vehicle
  position_from: str = Field(..., alias='_from')
  position_to: str = Field(..., alias='_to')
  type: InventoryMovementType

  product_key: str | None = None
  serial_key: str | None = None

  # quantity: float | None --> This doesn't get into the model but is used from InventoryMovementNew and parsed into qt_planned/confirmed
  qt_planned: float | None = 1
  qt_confirmed: float | None = 0

  status: MovementStatus | None = MovementStatus.PLANNED
  created: datetime | None = None
  start: datetime | None = None
  end: datetime | None = None
  inverse_movement_key: str | None = None # link to the movement that is the reversal of this movement

  movement_list_key: str | None = None # link to MovementList document, if present
  movement_list_item: float | None = None # "row" number in the movement list

  references: InventoryMovementReferences | None = None # RECEIPTS: purchase doc, SHIPMENTS: sales doc, TRANSFERS/PROD/CONS: work order/job
  reason: str | None = None

  user_key: str | None = None

  extra: Any = None

  @field_validator('qt_planned', 'qt_confirmed', mode='before')
  @classmethod
  def round_float_fields(cls, v):
    """Round float fields to prevent floating-point precision noise."""
    if isinstance(v, float):
      return round_float(v)
    return v

  # Transfer routes must have at least two positions. Positions must be repeat.
  @model_validator(mode='after')
  def validate(self):
    # validate dates
    if (
      self.status == MovementStatus.STARTED
      and self.start is None
    ):
      raise ValueError("Started movements must have a start date")

    if (
      self.status == MovementStatus.COMPLETED
      and (self.start is None or self.end is None)
    ):
      raise ValueError("Completed movements must have both a start and end date")

    if (
      self.product_key is None and self.serial_key is None and self.position_from is None
    ):
      raise ValueError("A movement must have a product, serial or container position")

    if self.position_from is None or self.position_to is None:
      raise ValueError("A movement must have a position from and to")
    return self


class MovementSplitData(BaseModel):
  position_from: str | None = None
  position_to: str | None = None
  serial_key: str | None = None
  serial_code: str | None = None
  qt_confirmed: float
  qt_planned: float | None = None

  @field_validator('qt_confirmed', 'qt_planned', mode='before')
  @classmethod
  def round_float_fields(cls, v):
    """Round float fields to prevent floating-point precision noise."""
    if isinstance(v, float):
      return round_float(v)
    return v

  @model_validator(mode='after')
  def set_qt_planned(self):
    if self.qt_planned is None:
      self.qt_planned = self.qt_confirmed
    return self

class InventoryMovementUpdate(InventoryMovement):
  split_into: list[MovementSplitData] | None = []

class InventoryMovementSearchParameters(BaseModel):
  movement_type: InventoryMovementType | None = None
  movement_status: MovementStatus | None = None
  include_planned: bool | None = True
  include_completed: bool | None = True
  start_from: datetime | None = None
  start_to: datetime | None = None
  end_from: datetime | None = None
  end_to: datetime | None = None
  product_key: str | None = None
  product_search: WildcardString = None
  serial_keys: list[str] | None = None
  serial_search: WildcardString = None
  list_key: list[str] | None = None
  list_search: str | None = None
  work_order_search: WildcardString = None
  position_from: str | None = None
  position_to: str | None = None
  position_filter_operator: str | None = 'AND'
  limit: int | None = 500
  offset: int | None = 0
  search_graph: bool | None = True


class InventoryMovementSearchResults(InventoryMovement):
  position_from_key: str | None = None
  position_from_code: str | None = None
  position_to_key: str | None = None
  position_to_code: str | None = None
  movement_list_code: str | None = None
  product_key: str | None = None
  product_code: str | None = None
  product_description: str | None = None
  serial_key: str | None = None
  serial_code: str | None = None
  qt_planned: float | None = None
  qt_confirmed: float | None = None
  references: InventoryMovementReferences | None = None





# ========================================================
# MOVEMENT LISTS
# ========================================================

class MovementList(ArangoDocument):
  """
  The model implies movement references do NOT conflict with the list references.
  TODO: enforce consistency at the model level or in the `merge_references` function
  """
  #code: str | None = Field(default_factory=_generate_counter('default'))
  # keep code mandatory until completion of list counter setup
  code: Annotated[str, StringConstraints(to_upper=True)]
  notes: str | None = None
  due_by: date | None = Field(default_factory=date.today)
  created: datetime | None = Field(default_factory=timestamp)
  start: datetime | None = None
  end: datetime | None = None
  status: MovementStatus | None = MovementStatus.PLANNED
  extra: Any = None
  references: InventoryMovementReferences | None = None
  type: InventoryMovementType


class MovementListWithCounts(MovementList):
  counts: dict[MovementStatus, int]


class MovementListNewStatus(str, Enum):
  PLANNED = 'planned'
  COMPLETED = 'completed'

class MovementListNew(MovementList):
  status: MovementListNewStatus | None = MovementListNewStatus.PLANNED
  movements: list[InventoryMovementNew] | None = []
  by_code: bool | None = False

  @model_validator(mode='before')
  def validate(cls, values):

    # Ensure the list has a valid type
    if values.get('type', None) not in [t.value for t in InventoryMovementType]:
      raise ValueError("A movement list must have a valid type: valid types are: " + ", ".join([t.value for t in InventoryMovementType]))

    items_product = {}
    for movement in values.get('movements', []):

      # Ensure all movements in the list are of the same type
      if movement.get('movement_type') is not None and movement.get('movement_type') != values.get('type'):
        raise ValueError("All movements in a movement list must be of the same type")
      if movement.get('movement_type') is None:
        movement['movement_type'] = values['type']

      # Ensure all movements have a product reference
      product_ref = 'product_code' if values.get('by_code') else 'product_key'
      if movement.get(product_ref) is None:
        raise ValueError(f"{product_ref} is required for all movements. Missing for movement {movement}")

      # Prevent different products or multiple non-serial movements with same list item
      by_code = values.get('by_code')
      list_item = movement.get('movement_list_item')
      movement_serial = movement.get('serial_code' if by_code else 'serial_key')

      if items_product.get(list_item) is not None:
        if items_product.get(list_item).get('product') != movement.get(product_ref):
          raise ValueError(f"Cannot have multiple products with the same movement list item {list_item}")
        elif movement_serial in items_product.get(list_item).get('serials'):
          raise ValueError(f"Cannot have the same serial number or no serial number in multiple movements within the same list item (Item: {list_item})")
      else:
        items_product[list_item] = dict(product=movement.get(product_ref), serials=[movement_serial])

    return values

