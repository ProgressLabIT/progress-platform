from datetime import date, datetime
from enum import Enum
from typing import Any
from typing import Annotated


from pydantic import BaseModel, ConfigDict, Field, model_validator, StringConstraints

from models.base_models import ArangoDocument, ArangoEdge, FlexModel
#from utils.counter import _generate_counter
from utils.dt import timestamp


class InventoryCommandType(str, Enum):
  ADD_MOVEMENT = 'ADD_MOVEMENT'
  UPDATE_MOVEMENT = 'UPDATE_MOVEMENT'
  DELETE_MOVEMENT = 'DELETE_MOVEMENT'

class InventoryNotificationType(str, Enum):
  ERROR = 'ERROR'
  MOVEMENT_ADDED = 'MOVEMENT_ADDED'


class InventoryNotificationErrorCode(str, Enum):
  EXCEPTION = 'EXCEPTION'

class InventoryGlobalConfig(ArangoDocument):
  allow_placement_different_from_planned: bool = True
  allow_mission_closing_with_unstarted_movements: bool = False # started movements must be completed


class InventoryUsagePolicy(str, Enum):
  FIFO = 'fifo',
  LIFO = 'lifo',
  CLOSEST_TO_EXPIRATION = 'closest_to_expiration' # may be different than FIFO due to different expiration times since receipt


class Position(ArangoDocument):
  code: str | None = None
  owned: bool | None = True
  available: bool | None = True
  disposable: bool | None = False # gets deleted when emptied or shipped
  fixed: bool | None = True
  deleted: bool | None = False
  created: datetime | None = Field(default_factory=timestamp)
  allow_consumption: bool | None = None
  extra: Any = None

class PositionNew(FlexModel):
  parent_position_key: str | None = 'IN'
  code: str | None = None
  owned: bool | None = True
  available: bool | None = True
  fixed: bool | None = True
  disposable: bool | None = False
  allow_consumption: bool | None = None
  extra: Any = None


class PositionLink(ArangoEdge):  #edge is_in_position
 """
 the is_in_position collection is used both for inventory and for position hierarchy.
 This class is only used to distinguish what we're using the collection for.
 """
 pass


class PositionSearchParams(BaseModel):
  search: str | None = None
  has_product_key: list[str] | None = None
  has_product_code: list[str] | None = None
  is_in_position: str | None = None
  contains_position: str | None = None
  #include_non_disposable: bool | None = True
  #include_disposable: bool | None = True
  #include_owned: bool | None = True
  #include_not_owned: bool | None = True
  #include_deleted: bool | None = False  //include deleted non ha tanto senso perchè tanto non c'è piu' il link quindi non la trova lo stesso
  limit: int | None = 200
  offset: int | None = 0


class Inventory(BaseModel): # edge is_in_position
  model_config = ConfigDict(populate_by_name=True)

  product_id: str = Field(..., alias='_from')
  position_id: str = Field(..., alias='_to')
  serial_key: str | None = None
  quantity: float
  owned: bool = True # False means it's property of customers or suppliers
  value: float | None = None
  date_received: datetime | None = None
  expiration_date: datetime | None = None
  extra: Any = None

class InventorySearchResult(BaseModel):
  product_code: str | None = None
  position_code: str | None = None
  serial_code: str | None = None
  serial_key: str | None = None
  product_key: str | None = None
  position_key: str | None = None
  quantity: float
  owned: bool = True
  value: float | None = None
  reference: str | None = None
  date_received: datetime | None = None
  expiration_date: datetime | None = None
  extra: Any = None


class InventorySearchParams(BaseModel):
  #TODO uncomment
  product_key: str | None = None
  product_code: str | None = None
  position_key: str | None = None
  position_code: str | None = None
  serial_keys: list[str] | None = None
  # serial_code: str | None = None
  owned: bool | None = None
  limit: int | None = 200
  offset: int | None = 0
  strict: bool | None = False

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

class InventoryMovementReferences(BaseModel):
  work_order_key: str | None = None
  job_key: str | None = None
  batch_key: str | None = None
  event_key: str | None = None
  event_group_key: str | None = None
  transfer_doc: str | None = None
  sales_doc: str | None = None
  purchase_doc: str | None = None
  partner_name: str | None = None # supplier/customer name
  partner_code: str | None = None # supplier/customer code


class InventoryMovementNew(FlexModel):
  position_from: str = Field(..., alias='_from')
  position_to: str | None = Field('Position/IN', alias='_to')
  type: InventoryMovementType | None = None
  status: MovementStatus | None = MovementStatus.COMPLETED
  product_key: str | None = None
  serial_key: str | None = None
  serial_code: str | None = None
  quantity: float | None = 1
  start: datetime | None = None
  end: datetime | None = None
  source: InventoryMovementReferences | None = None
  reason: str | None = None
  user_key: str | None = None
  extra: Any = None

  @model_validator(mode='before')
  def set_default_values(cls, values):
    if values.get('type') == InventoryMovementType.RECEIPT.value:
      values['_from'] = 'Position/OUT'
    if values.get('type') == InventoryMovementType.SHIPMENT.value:
      values['_to'] = 'Position/OUT'
    if values.get('status') in [MovementStatus.STARTED.value, MovementStatus.COMPLETED.value] and values.get('start', None) is None:
      values['start'] = timestamp()
    if values.get('status') == MovementStatus.COMPLETED.value and values.get('end', None) is None:
      values['end'] = timestamp()
    return values

  @model_validator(mode='after')
  def validate(self):
    if self.product_key is None and self.product_code is None:
      raise ValueError("A movement must have a product")
    if self.serial_key is not None and self.qt_planned > 1:
      raise ValueError("A serial movement must have a quantity of 1")
    if self.position_from == self.position_to:
      raise ValueError("A movement must have a different position from and to")
    return self


class InventoryMovement(ArangoEdge): # edge collection movement
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
  created: datetime = Field(default_factory=timestamp)
  start: datetime | None = None
  end: datetime | None = None

  movement_list_key: str | None = None # link to MovementList document, if present

  source: InventoryMovementReferences | None = None # RECEIPTS: purchase doc, SHIPMENTS: sales doc, TRANSFERS/PROD/CONS: work order/job
  reason: str | None = None

  user_key: str | None = None

  extra: Any = None

  @model_validator(mode='before')
  def parse_quantity(cls, values):
    if values.get('quantity', None) is not None:
      values['qt_planned'] = values['quantity']
      if values.get('status', None) == MovementStatus.COMPLETED.value:
        values['qt_confirmed'] = values['quantity']
    return values

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

    if self.type == InventoryMovementType.TRANSFER and (self.position_from is None or self.position_to is None):
      raise ValueError("A transfer movement must have a position from and to")

    return self

class InventoryMovementEvent(InventoryMovementNew):
  quantity: float | None = None

class InventoryMovementSearchParameters(BaseModel):
  movement_type: InventoryMovementType | None = None
  movement_status: MovementStatus | None = None
  include_planned: bool | None = True
  start_from: datetime | None = None
  start_to: datetime | None = None
  end_from: datetime | None = None
  end_to: datetime | None = None
  product_key: str | None = None
  product_code: str | None = None
  serial_keys: list[str] | None = None
  list_key: str | None = None
  list_code: str | None = None
  # source: InventoryMovementSource | None = None
  position_from: str | None = None
  position_to: str | None = None
  position_filter_operator: str | None = 'AND'
  limit: int | None = 500
  offset: int | None = 0

class InventoryMovementSearchResults(InventoryMovement):
  position_from_key: str | None = None
  position_from_code: str | None = None
  position_to_key: str | None = None
  position_to_code: str | None = None
  product_key: str | None = None
  product_code: str | None = None
  serial_key: str | None = None
  serial_code: str | None = None
  qt_planned: float | None = None
  qt_completed: float | None = None
  source: InventoryMovementReferences | None = None



class MovementList(ArangoDocument):
  #code: str | None = Field(default_factory=_generate_counter('default'))
  code: Annotated[str, StringConstraints(to_upper=True)] | None = None
  notes: str | None = None
  due_by: date | None = None
  created: datetime | None = Field(default_factory=timestamp)
  start: datetime | None = None
  end: datetime | None = None
  status: MovementStatus | None = MovementStatus.PLANNED
  extra: Any = None
  source: InventoryMovementReferences | None = None
  type: InventoryMovementType | None = None


class MovementListNew(MovementList):
  movements: list[InventoryMovementNew] | None = None
  by_code: bool | None = False

  @model_validator(mode='after')
  def validate(self):
    if self.movements is None or len(self.movements) == 0:
      raise ValueError("A movement list must have at least one movement")
    for movement in self.movements:
      if movement.position_from is None or movement.position_to is None:
        raise ValueError("A movement must have a position from and to")
      if movement.type != self.type:
        raise ValueError("All movements in a movement list must be of the same type")
    return self
