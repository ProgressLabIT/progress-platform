from datetime import date, datetime
from enum import Enum
from typing import Any
from typing import Annotated


from pydantic import BaseModel, model_validator, Field, StringConstraints

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
  deleted: bool | None = False
  created: datetime | datetime = Field(default_factory=timestamp)
  extra: Any = None

class PositionNew(FlexModel):
  parent_position_key: str | None = 'IN'
  code: str | None = None
  owned: bool | None = True
  available: bool | None = True
  disposable: bool | None = False
  deleted: bool | None = False
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


class Inventory(ArangoDocument): # edge is_in_position
  product_id: str = Field(..., alias='_from')
  position_id: str = Field(..., alias='_to')
  serial_key: str | None = None
  quantity: float
  owned: bool = True # False means it's property of customers or suppliers
  value: float | None = None
  reference: str | None # entry transport document, traceability event, etc.
  date_received: date | None = Field(default_factory=timestamp)
  expiration_date: date | None = None
  extra: Any = None


class InventorySearchParams(BaseModel):
  product_key: str | None = None
  product_code: str | None = None
  position_key: str | None = None
  position_code: str | None = None
  # include_child_positions: str | None = False
  serial_key: str | None = None
  serial_code: str | None = None
  owned: bool | None = None

class MovementStatus(str, Enum):
  PLANNED = 'planned'
  STARTED = 'started'
  COMPLETED = 'completed'
  CANCELED = 'canceled'


class WarehouseMission(ArangoDocument):
  #code: str | None = Field(default_factory=_generate_counter('default'))
  code: Annotated[str, StringConstraints(to_upper=True)] | None = None
  notes: str | None = None
  due_by: date | None = None
  assigned_to: str | None = None
  created: datetime | None = Field(default_factory=timestamp)
  start: datetime | None = None
  end: datetime | None = None
  status: MovementStatus | None = MovementStatus.PLANNED
  extra: Any = None


class InventoryMovementType(str, Enum):
  TRANSFER = 'transfer'
  RECEIPT = 'receipt'
  SHIPMENT = 'shipment'
  PRODUCTION = 'production'
  CONSUMPTION = 'consumption'
  ADJUSTMENT = 'adjustment'

class InventoryMovement(ArangoEdge): # edge collection movement
  # can be a segment of a multistep movement (to be used as graph),
  # in case material needs to be assigned a specific position in e.g. a transfer trolley with codified shelves
  # or in the future via a specific transport vehicle
  position_from: str = Field(..., alias='_from')
  position_to: str = Field(..., alias='_to')
  type: InventoryMovementType

  product_key: str
  serial_key: str | None = None
  qt_planned: float
  qt_confirmed: float

  status: MovementStatus | None = MovementStatus.PLANNED
  created: datetime = Field(default_factory=timestamp)
  start: datetime | None = None
  end: datetime | None = None

  mission_key: str | None = None # link to WarehouseMission document, if present

  movement_doc: str | None = None # RECEIPTS/SHIPMENTS: transport document, TRANSFERS: na, PROD/CONS: na
  source_doc: str | None = None # RECEIPTS: purchase doc, SHIPMENTS: sales doc, TRANSFERS/PROD/CONS: work order/job

  user_key: str | None = None
  extra: Any = None

  # Transfer routes must have at least two positions. Positions must be repeat.
  @model_validator(mode='after')
  def validate(self):
    # validate route
    if self.type == InventoryMovementType.TRANSFER:
      length = len(self.route)
      if length < 2 and len(set(self.route)) != length:
        raise ValueError("Movement route must contain at least two positions and positions must not repeat")

    # validate dates
    if (
      self.status == MovementStatus.STARTED
      and self.start is None
    ):
      raise ValueError("In transfer movements must have a start date")

    if (
      self.status == MovementStatus.COMPLETED
      and (self.start is None or self.end is None)
    ):
      raise ValueError("Completed movements must have both a start and end date")

    return self

class InventoryMovementEvent(InventoryMovement):
  quantity: float | None = None

class InventoryMovementSearchParameters(BaseModel):
  movement_type: InventoryMovementType | None = None
  movement_status: MovementStatus | None = None
  include_planned: bool | None = False
  start_from: datetime | None = None
  start_to: datetime | None = None
  end_from: datetime | None = None
  end_to: datetime | None = None
  product_key: str | None = None
  product_code: str | None = None
  serial_key: str | None = None
  serial_code: str | None = None
  mission_key: str | None = None
  mission_code: str | None = None
  movement_doc: str | None = None
  source_doc: str | None = None
  position_from: str | None = None
  position_to: str | None = None
  limit: int | None = 500
  offset: int | None = 0

class InventoryMovementSearchResults(InventoryMovement):
  position_from_code: str | None = None
  position_to_code: str | None = None
  product_code: str | None = None
