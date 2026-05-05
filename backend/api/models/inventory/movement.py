from datetime import date, datetime
from enum import Enum
from typing import Any
from typing import Annotated


from pydantic import BaseModel, ConfigDict, Field, model_validator, StringConstraints, field_serializer

from models.base_models import ArangoDocument, FlexModel
#from utils.counter import _generate_counter
from utils.dt import timestamp
from utils.search import WildcardString



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
  work_order_key: str | None = Field(None, description="Key of the work order that triggered this movement.", examples=["WO-2026-001"])
  job_key: str | None = Field(None, description="Key of the job that triggered this movement.", examples=["job/job-2026-001"])
  batch_key: str | None = Field(None, description="Key of the production batch associated with this movement.", examples=["BATCH-A-042"])
  origin_movement_key: str | None = Field(None, description="Key of the original movement that this record reverses or splits.", examples=["mvt-001"])
  transfer_doc: str | None = Field(None, description="External transfer document reference.", examples=["TRF-2026-0042"])
  sales_doc: str | None = Field(None, description="External sales document reference (e.g. delivery note).", examples=["DN-2026-0042"])
  purchase_doc: str | None = Field(None, description="External purchase document reference (e.g. goods receipt).", examples=["GR-2026-0042"])
  partner_name: str | None = Field(None, description="Name of the supplier or customer involved.", examples=["Acme Supplies Ltd"])
  partner_code: str | None = Field(None, description="Code of the supplier or customer involved.", examples=["ACME-001"])
  inventory_count_session_key: str | None = Field(None, description="Key of the count session that generated this adjustment movement.", examples=["cnt-session-001"])


class InventoryMovementNew(FlexModel):
  model_config = ConfigDict(populate_by_name=True)

  position_from: str | None = Field(None, serialization_alias='_from', description="Source position key or virtual constant (`IN`, `OUT`, `NULL`). Auto-set for production/consumption/shipment/receipt types.", examples=["12345", "OUT"])
  position_to: str | None = Field(None, serialization_alias='_to', description="Destination position key or virtual constant. Auto-set for production/consumption/shipment/receipt types.", examples=["67890", "IN"])
  movement_type: InventoryMovementType = Field(..., serialization_alias='type', description="Type of inventory movement.", examples=["transfer"])
  status: MovementStatus | None = Field(MovementStatus.COMPLETED, description="Initial status of the movement.", examples=["completed"])
  product_key: str | None = Field(None, description="Key of the product being moved. Required unless a container position transfer is specified.", examples=["67890"])
  product_code: str | None = Field(None, description="Code of the product (alternative to `product_key` when `by_code=True`).", examples=["PROD-001"])
  serial_key: str | None = Field(None, description="Key of the serial number being moved. Serial movements must have quantity ±1.", examples=["SN-LR-001234"])
  serial_code: str | None = Field(None, description="Serial code (alternative to `serial_key` when `by_code=True`).", examples=["SN-LR-001234"])
  qt_planned: float | None = Field(1, description="Planned quantity for the movement.", examples=[100.0])
  qt_confirmed: float | None = Field(0, description="Confirmed quantity actually moved.", examples=[100.0])
  created: datetime | None = Field(default_factory=timestamp, description="Timestamp when the movement record was created.", examples=["2026-05-15T10:00:00Z"])
  start: datetime | None = Field(None, description="Timestamp when the movement was started.", examples=["2026-05-15T10:00:00Z"])
  end: datetime | None = Field(None, description="Timestamp when the movement was completed.", examples=["2026-05-15T10:05:00Z"])
  movement_list_key: str | None = Field(None, description="Key of the `MovementList` this movement belongs to, if any.", examples=["mvtlist-001"])
  movement_list_item: float | None = Field(None, description="Row number within the movement list (used for grouping multi-row lists).", examples=[1.0])
  references: InventoryMovementReferences | None = Field(None, description="External references linking this movement to business documents.", examples=[None])
  reason: str | None = Field(None, description="Free-text reason for the movement (e.g. for adjustments).", examples=["Annual stock adjustment"])
  user_key: str | None = Field(None, description="Key of the user who performed the movement.", examples=["user/operator-01"])
  extra: Any = Field(None, description="Arbitrary extra metadata.", examples=[None])

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
  position_from: str = Field(..., alias='_from', description="ArangoDB document ID of the source position (`Position/<key>`).", examples=["Position/12345"])
  position_to: str = Field(..., alias='_to', description="ArangoDB document ID of the destination position (`Position/<key>`).", examples=["Position/67890"])
  type: InventoryMovementType = Field(..., description="Type of inventory movement.", examples=["transfer"])

  product_key: str | None = Field(None, description="Key of the product involved in the movement.", examples=["67890"])
  serial_key: str | None = Field(None, description="Key of the serial number involved, for serialized products.", examples=["SN-LR-001234"])

  # quantity: float | None --> This doesn't get into the model but is used from InventoryMovementNew and parsed into qt_planned/confirmed
  qt_planned: float | None = Field(1, description="Planned quantity.", examples=[100.0])
  qt_confirmed: float | None = Field(0, description="Confirmed quantity actually moved.", examples=[100.0])

  status: MovementStatus | None = Field(MovementStatus.PLANNED, description="Current status of the movement.", examples=["completed"])
  created: datetime | None = Field(None, description="Timestamp when the movement was created.", examples=["2026-05-15T10:00:00Z"])
  start: datetime | None = Field(None, description="Timestamp when the movement was started.", examples=["2026-05-15T10:00:00Z"])
  end: datetime | None = Field(None, description="Timestamp when the movement was completed.", examples=["2026-05-15T10:05:00Z"])
  inverse_movement_key: str | None = Field(None, description="Key of the reversal movement that cancels this movement.", examples=["mvt-reversal-001"])

  movement_list_key: str | None = Field(None, description="Key of the `MovementList` this movement belongs to.", examples=["mvtlist-001"])
  movement_list_item: float | None = Field(None, description="Row number within the movement list.", examples=[1.0])

  references: InventoryMovementReferences | None = Field(None, description="External references (work order, job, batch, purchase/sales documents).", examples=[None])
  reason: str | None = Field(None, description="Free-text reason for the movement.", examples=["Annual stock adjustment"])

  user_key: str | None = Field(None, description="Key of the user who performed the movement.", examples=["user/operator-01"])

  extra: Any = Field(None, description="Arbitrary extra metadata.", examples=[None])

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
  position_from: str | None = Field(None, description="Override source position for the split segment.", examples=["12345"])
  position_to: str | None = Field(None, description="Override destination position for the split segment.", examples=["67890"])
  serial_key: str | None = Field(None, description="Serial key for this split segment.", examples=["SN-LR-001234"])
  serial_code: str | None = Field(None, description="Serial code for this split segment.", examples=["SN-LR-001234"])
  qt_confirmed: float = Field(..., description="Confirmed quantity for this split segment.", examples=[50.0])
  qt_planned: float | None = Field(None, description="Planned quantity for this split segment; defaults to `qt_confirmed` if omitted.", examples=[50.0])

  @model_validator(mode='after')
  def set_qt_planned(self):
    if self.qt_planned is None:
      self.qt_planned = self.qt_confirmed
    return self

class InventoryMovementUpdate(InventoryMovement):
  split_into: list[MovementSplitData] | None = Field([], description="Optional list of split segments to replace this movement with.", examples=[[]])

class InventoryMovementSearchParameters(BaseModel):
  movement_type: InventoryMovementType | None = Field(None, description="Filter by movement type.", examples=["transfer"])
  movement_status: MovementStatus | None = Field(None, description="Filter by movement status.", examples=["completed"])
  include_planned: bool | None = Field(True, description="Include movements in `planned` status.", examples=[True])
  include_completed: bool | None = Field(True, description="Include movements in `completed` status.", examples=[True])
  start_from: datetime | None = Field(None, description="Filter movements that started on or after this timestamp.", examples=["2026-01-01T00:00:00Z"])
  start_to: datetime | None = Field(None, description="Filter movements that started on or before this timestamp.", examples=["2026-12-31T23:59:59Z"])
  end_from: datetime | None = Field(None, description="Filter movements that ended on or after this timestamp.", examples=["2026-01-01T00:00:00Z"])
  end_to: datetime | None = Field(None, description="Filter movements that ended on or before this timestamp.", examples=["2026-12-31T23:59:59Z"])
  product_key: str | None = Field(None, description="Filter by product key.", examples=["67890"])
  product_search: WildcardString = Field(None, description="Wildcard search on product code.", examples=["PROD-*"])
  serial_keys: list[str] | None = Field(None, description="Filter to movements involving any of these serial keys.", examples=[["SN-LR-001234"]])
  serial_search: WildcardString = Field(None, description="Wildcard search on serial code.", examples=["SN-LR-*"])
  list_key: list[str] | None = Field(None, description="Filter to movements belonging to any of these movement list keys.", examples=[["mvtlist-001"]])
  list_search: str | None = Field(None, description="Text search on movement list code.", examples=["LIST-2026"])
  work_order_search: WildcardString = Field(None, description="Wildcard search on work order code in references.", examples=["WO-2026-*"])
  position_from: str | None = Field(None, description="Filter by source position key.", examples=["12345"])
  position_to: str | None = Field(None, description="Filter by destination position key.", examples=["67890"])
  position_filter_operator: str | None = Field('AND', description="Logical operator for `position_from` / `position_to` filter combination (`AND` or `OR`).", examples=["AND"])
  limit: int | None = Field(500, description="Maximum number of results.", examples=[500])
  offset: int | None = Field(0, description="Pagination offset.", examples=[0])
  search_graph: bool | None = Field(True, description="If True, traverse the position graph when filtering by position.", examples=[True])


class InventoryMovementSearchResults(InventoryMovement):
  position_from_key: str | None = Field(None, description="Key of the source position.", examples=["12345"])
  position_from_code: str | None = Field(None, description="Code of the source position.", examples=["WAREHOUSE-A"])
  position_to_key: str | None = Field(None, description="Key of the destination position.", examples=["67890"])
  position_to_code: str | None = Field(None, description="Code of the destination position.", examples=["LOCATION-B2-03"])
  movement_list_code: str | None = Field(None, description="Code of the movement list this movement belongs to.", examples=["LIST-2026-001"])
  product_key: str | None = Field(None, description="Key of the product.", examples=["67890"])
  product_code: str | None = Field(None, description="Code of the product.", examples=["PROD-001"])
  product_description: str | None = Field(None, description="Description of the product.", examples=["Steel bracket M6"])
  serial_key: str | None = Field(None, description="Key of the serial number.", examples=["SN-LR-001234"])
  serial_code: str | None = Field(None, description="Code of the serial number.", examples=["SN-LR-001234"])
  qt_planned: float | None = Field(None, description="Planned quantity.", examples=[100.0])
  qt_confirmed: float | None = Field(None, description="Confirmed quantity.", examples=[100.0])
  references: InventoryMovementReferences | None = Field(None, description="External document references.", examples=[None])




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
  code: Annotated[str, StringConstraints(to_upper=True)] = Field(..., description="Unique movement list code (uppercase enforced).", examples=["LIST-2026-001"])
  notes: str | None = Field(None, description="Free-text notes for the movement list.", examples=["Replenishment from supplier WH"])
  due_by: date | None = Field(default_factory=date.today, description="Target completion date for the list.", examples=["2026-05-20"])
  created: datetime | None = Field(default_factory=timestamp, description="Timestamp when the list was created.", examples=["2026-05-15T10:00:00Z"])
  start: datetime | None = Field(None, description="Timestamp when the first movement in the list was started.", examples=["2026-05-15T10:00:00Z"])
  end: datetime | None = Field(None, description="Timestamp when the last movement in the list was completed.", examples=["2026-05-15T12:00:00Z"])
  status: MovementStatus | None = Field(MovementStatus.PLANNED, description="Aggregate status of the movement list.", examples=["planned"])
  extra: Any = Field(None, description="Arbitrary extra metadata.", examples=[None])
  references: InventoryMovementReferences | None = Field(None, description="External references shared by all movements in the list.", examples=[None])
  type: InventoryMovementType = Field(..., description="Type of movements in this list (all movements must match).", examples=["transfer"])


class MovementListWithCounts(MovementList):
  counts: dict[MovementStatus, int] = Field(..., description="Aggregated count of movements per status.", examples=[{"planned": 3, "completed": 7}])


class MovementListNewStatus(str, Enum):
  PLANNED = 'planned'
  COMPLETED = 'completed'

class MovementListNew(MovementList):
  status: MovementListNewStatus | None = Field(MovementListNewStatus.PLANNED, description="Initial status of the new movement list.", examples=["planned"])
  movements: list[InventoryMovementNew] | None = Field([], description="List of movements to create as part of this list.", examples=[[]])
  by_code: bool | None = Field(False, description="If True, movements are matched to products and serials by code instead of key.", examples=[False])

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
