from datetime import date
from enum import Enum
from typing import Any

from pydantic import model_validator, field_validator, Field

from models.base_models import ArangoDocument
from utils.counter import _generate_counter
from utils.dt import timestamp

class InventoryUsagePolicy(str, Enum):
  FIFO = 'fifo',
  LIFO = 'lifo',
  CLOSEST_TO_EXPIRATION = 'closest_to_expiration' # may be different than FIFO due to different expiration times since receipt


class Position(ArangoDocument):
  code: str
  owned: bool | None = True
  disposable: bool | None = False # gets deleted when emptied
  extra: Any = None


class Inventory(ArangoDocument): # edge located_in
  product_id: str = Field(..., alias='_from')
  location_id: str = Field(..., alias='_to')
  serial_key: str | None = None
  quantity: float
  owned: bool = True # False means it's property of customers or suppliers
  value: float | None = None
  reference: str | None # entry transport document, traceability event, etc.
  date_received: date | None = Field(default_factory=timestamp)
  expiration_date: date | None = None
  extra: Any = None



class WarehouseMission(ArangoDocument):
  code: str | None = Field(default_factory=_generate_counter('default'))
  notes: str | None = None
  due_by: date | None = None
  assigned_to: str | None = None
  extra: Any = None



class InventoryMovementType(str, Enum):
  TRANSFER = 'transfer'
  RECEIPT = 'receipt'
  SHIPMENT = 'shipment'
  PRODUCTION = 'production'
  CONSUMPTION = 'consumption'
  ADJUSTMENT = 'adjustment'


class MovementStatus(str, Enum):
  PLANNED = 'planned'
  STARTED = 'started'
  COMPLETED = 'completed'
  CANCELED = 'canceled'


class InventoryMovement(ArangoDocument):
  type: InventoryMovementType

  product_key: str
  serial_key: str | None = None
  qt_planned: float
  qt_confirmed: float

  route: list[str] | None = None
  # can be a multistep movement, listing in order all the positions it needs to go through,
  # in case it needs to be assigned a specific position in e.g. a transfer trolley with codified shelves

  stage: int | None = None
  # index of the latest confirmed route position

  status: MovementStatus | None = MovementStatus.PLANNED
  created: datetime = Field(default_factory=timestamp)
  start: datetime | None = None
  end: datetime | None = None

  mission_key: str | None = None # link to WarehouseMission document, if present

  reference: str | None = None # link to work order, job, project, etc.

  extra: Any = None

  # Transfer routes must have at least two positions. Positions must be repeat.
  @model_validator('after')
  def validate_route(self):
    if self.type == InventoryMovementType.TRANSFER:
      length = len(self.route)
      if length < 2 and len(set(self.route)) != length:
        raise ValueError("Movement route must contain at least two positions and positions must not repeat")
    return self


  # Ensure start date is present if
  @model_validator(mode='after')
  def ensure_dates(self):
    if (
      self.status == MovementStatus.STARTED
      and self.start is None
    ):
      raise ValueError("In transfer movements must have a start date")
    elif (
      self.status != MovementStatus.COMPLETED
      and (self.start is None or self.end is None)
    ):
      raise ValueError("Completed movements must have both a start and end date")
    else:
      return self
