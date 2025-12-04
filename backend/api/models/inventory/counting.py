from datetime import datetime
from enum import Enum
from typing import Any, Literal


from pydantic import Field, model_validator, BaseModel

from models.base_models import ArangoDocument
from utils.dt import timestamp
from utils.search import WildcardString
from utils.dt import timestamp



# ========================================================
# STOCK COUNTING
# ========================================================

class InventoryCountSessionStatus(str, Enum):
  PLANNED = 'planned'
  STARTED = 'started'
  COMPLETED = 'completed'
  APPLIED = 'applied'
  CANCELED = 'canceled'

class InventoryCountSessionType(str, Enum):
  BY_POSITION = 'position'
  BY_PRODUCT = 'product'

class InventoryCountSession(ArangoDocument):
  code: str | None = None  # Auto-generated from counter if not provided
  description: str | None = None
  type: InventoryCountSessionType
  status: InventoryCountSessionStatus = InventoryCountSessionStatus.PLANNED
  blind_quantities: bool = True  # Hide expected quantities from operators
  blind_serials: bool = True  # Hide serial numbers from operators
  coverage_percentage: float | None = None  # Calculated field

  # Schedule
  scheduled_start: datetime | None = None
  scheduled_end: datetime | None = None

  # Audit trail
  created: datetime = Field(default_factory=timestamp)
  created_by: str | None = None  # user_key
  started: datetime | None = None
  completed: datetime | None = None

  baseline_snapshot_key: str | None = None
  post_count_snapshot_key: str | None = None
  post_adjustment_snapshot_key: str | None = None
  adjustment_list_key: str | None = None  # Link to final MovementList

  # Metadata
  notes: str | None = None
  extra: Any = None

class InventoryCountAssignmentStatus(str, Enum):
  PLANNED = 'planned'
  STARTED = 'started'
  COMPLETED = 'completed'
  CANCELED = 'canceled'


class InventoryCountSessionUpdate(BaseModel):
  code: str | None = None
  description: str | None = None
  type: InventoryCountSessionType | None = None
  blind_quantities: bool | None = None
  blind_serials: bool | None = None
  scheduled_start: datetime | None = None
  scheduled_end: datetime | None = None
  notes: str | None = None

class InventoryCountSessionSearchParams(BaseModel):
  search: WildcardString = None
  status: InventoryCountSessionStatus | None = None
  type: InventoryCountSessionType | None = None
  limit: int | None = 500
  offset: int | None = 0


class InventoryCountAssignmentNew(BaseModel):
  user_key: str
  target_keys: list[str]

class InventoryCountAssignment(ArangoDocument):
  inventory_count_session_key: str  # Parent campaign

  # What was assigned
  target_type: InventoryCountSessionType  # What was assigned
  target_key: str # Product key or position key

  # Assignment tracking
  assigned_to: str | None = None  # user_key, None means unstarted

  # Execution tracking
  status: InventoryCountAssignmentStatus | None = InventoryCountAssignmentStatus.PLANNED
  created: datetime = Field(default_factory=timestamp)
  created_by: str | None = None  # user_key
  started: datetime | None = None
  completed: datetime | None = None

  notes: str | None = None
  extra: Any = None


class InventoryCountAssignmentSearchParams(BaseModel):
  inventory_count_session_key: str | None = None
  assignment_type: InventoryCountSessionType | None = None
  product_key: str | None = None
  product_search: WildcardString = None
  position_key: str | None = None
  position_search: WildcardString = None
  assigned_to: str | None = None
  status: InventoryCountAssignmentStatus | None = None
  order_by: Literal['product', 'position'] | None = None
  limit: int | None = 500
  offset: int | None = 0

  def model_dump(self, *args, **kwargs):
    """Transforms category into record attribute name"""
    data = super().model_dump(*args, **kwargs)
    if self.order_by:
      data['order_by'] = f"{self.order_by}_key"
    return data


class InventoryCountStatus(str, Enum):
  STARTED = 'started'
  COMPLETED = 'completed'
  SUBMITTED = 'submitted'
  CONFIRMED = 'confirmed'
  DISCARDED = 'discarded'

class InventoryCountRecord(ArangoDocument): # edge collection inventory_count_record
  # What was counted
  product_id: str = Field(..., alias='_from')
  position_id: str = Field(..., alias='_to')

  # Core data - see validation below for ensuring correct setting
  system_qt: float # Snapshot at count time. Must be retaken in case count is updated before submission
  system_serial_keys: list[str] | None = None
  system_at: datetime | None = Field(default_factory=timestamp)

  counted_qt: float | None = None # Will always be set. See validation below
  counted_serial_keys: list[str] | None = None
  counted_at: datetime | None = None

  # Metadata
  inventory_count_session_key: str
  assignment_key: str | None = None
  user_key: str | None = None # User who started the count
  status: InventoryCountStatus = InventoryCountStatus.STARTED
  reviewed_at: datetime | None = None # Either confirmed or discarded
  notes: str | None = None
  extra: Any = None

  @property
  def product_key(self) -> str:
    return self.product_id.split('/')[-1]

  @property
  def position_key(self) -> str:
    return self.position_id.split('/')[-1]

  @property
  def delta(self) -> float | None:
    return self.counted_qt - self.system_qt

  @model_validator(mode='after')
  def handle_serials(self):
    # Ensure actual counts are recorded correctly
    if self.status != InventoryCountStatus.STARTED:
      if self.counted_serial_keys is not None:
        serial_count = len(self.counted_serial_keys)
        if self.counted_qt is None:
          self.counted_qt = serial_count
        elif self.counted_qt != serial_count:
          raise ValueError(
            "serial qt must be equal to the number of serial_keys if provided: "
            f"Serial qt: {self.counted_qt}, serial_count: {serial_count}"
          )
      elif self.counted_qt is None:
        raise ValueError("You must provide either a counted quantity or a list of serial keys found")
    return self


class InventoryCountRecordSearchParams(BaseModel):
  count_session_key: str | None = None
  user_key: str | None = None
  assignment_key: str | None = None
  product_key: str | None = None
  position_key: str | None = None
  include_started: bool = True
  include_completed: bool = True
  include_discarded: bool = True
  limit: int | None = 500
  offset: int | None = 0

class InventorySnapshotSource(str, Enum):
  IMPORT = 'import'
  MRP = 'mrp'
  COUNT_SESSION = 'count_session'

class InventorySnapshotType(str, Enum):
  VIRTUAL = 'virtual'
  ACTUAL = 'actual'

class InventorySnapshotScopeType(str, Enum):
  FULL = 'full'
  POSITIONS = 'positions'
  PRODUCTS = 'products'

class InventorySnapshot(ArangoDocument):
  snapshot_type: InventorySnapshotType
  source: InventorySnapshotSource
  inventory_count_session_key: str | None = None
  timestamp: datetime = Field(default_factory=timestamp)

  # Scope
  scope_type: InventorySnapshotScopeType = InventorySnapshotScopeType.FULL
  target_keys: list[str] | None = None

  created_by: str | None = None
  notes: str | None = None
  extra: Any = None

  @model_validator(mode='after')
  def validate_session_relationship(self):
    # Session snapshots MUST have a session reference
    if self.source == InventorySnapshotSource.COUNT_SESSION and not self.inventory_count_session_key:
      raise ValueError("Count session snapshots must have a session reference")

    return self

class InventorySnapshotItem(ArangoDocument): # edge collection
  product_key: str = Field(..., alias='_from')
  position_key: str = Field(..., alias='_to')
  inventory_snapshot_key: str
  quantity: float
  value: float | None = None
  serial_keys: list[str] | None = None
