from datetime import datetime
from enum import Enum
from typing import Any


from pydantic import Field, computed_field

from models.base_models import ArangoDocument, ArangoEdge
from utils.dt import timestamp




# ========================================================
# STOCK COUNTING
# ========================================================

class InventoryCountSessionStatus(str, Enum):
  PLANNED = 'planned'
  STARTED = 'started'
  REVIEW = 'review'
  COMPLETED = 'completed'
  CANCELED = 'canceled'

class InventoryCountSessionType(str, Enum):
  FULL = 'full'
  CYCLE_POSITION = 'cycle_position'
  CYCLE_PRODUCT = 'cycle_product'
  SPOT = 'spot'

class InventoryCountSession(ArangoDocument):
  code: str  # Auto-generated from counter
  description: str | None = None
  type: InventoryCountSessionType
  status: InventoryCountSessionStatus = InventoryCountSessionStatus.DRAFT
  blind_mode: bool = True  # Hide expected quantities from operators
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
  adjustment_list_key: str | None = None  # Link to final MovementList
  post_adjustment_snapshot_key: str | None = None

  # Metadata
  notes: str | None = None
  extra: Any = None

class InventoryCountAssignmentStatus(str, Enum):
  PLANNED = 'planned'
  STARTED = 'started'
  COMPLETED = 'completed'
  CANCELED = 'canceled'

class InventoryCountAssignmentType(str, Enum):
  POSITION = 'position'
  PRODUCT = 'product'

class InventoryCountAssignment(ArangoDocument):
  inventory_count_session_key: str  # Parent campaign

  # What was assigned
  assignment_type: InventoryCountAssignmentType  # What was assigned
  product_key: str | None = None # product key
  position_key: str | None = None # position key
  include_children: bool = True  # For position hierarchies

  # Assignment tracking
  assigned_to: str | None = None  # user_key, None means unstarted

  # Execution tracking
  status: InventoryCountAssignmentStatus = InventoryCountAssignmentStatus.PLANNED
  started: datetime | None = None
  completed: datetime | None = None

  notes: str | None = None
  extra: Any = None




class InventoryCountStatus(str, Enum):
  DRAFT = 'draft'
  COUNTED = 'counted'
  CONFIRMED = 'confirmed'
  DISCARDED = 'discarded'

class InventoryCount(ArangoDocument):
  inventory_count_session_key: str
  assignment_key: str

  # What was counted
  product_key: str
  position_key: str
  serial_keys: list[str] | None = None

  # The count
  system_qt: float  # Snapshot at count time
  count: float  # What the operator entered
  delta: float | None = None  # Calculated: count - system_quantity

  # Metadata
  counted_at: datetime
  confirmed_at: datetime | None = None
  confirmed_by: str | None = None

  # Audit trail
  inventory_snapshot_key: str | None = None  # Link to snapshot

  notes: str | None = None
  extra: Any = None

  @computed_field
  @property
  def product_id(self) -> str:
    return f'Product/{self.product_key}'

  @computed_field
  @property
  def position_id(self) -> str:
    return f'Position/{self.position_key}'


class InventorySnapshotReason(str, Enum):
  BASELINE = 'baseline'  # Taken at campaign start
  POST_COUNT = 'post_count'  # Before applying adjustments
  POST_ADJUSTMENT = 'post_adjustment'  # After applying adjustments
  FORECAST = 'forecast'  # Used for planning purposes (e.g. for MRP)
  MANUAL = 'manual'  # User-created snapshot

class InventorySnapshotSource(str, Enum):
  COUNT = 'count'
  IMPORT = 'import'
  MRP = 'mrp'
  USER = 'user'
  SYSTEM = 'system'

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
  reason: InventorySnapshotReason
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
    if self.reason in [
      InventorySnapshotReason.BASELINE,
      InventorySnapshotReason.POST_COUNT,
      InventorySnapshotReason.POST_ADJUSTMENT
    ]:
      if not self.inventory_count_session_key:
        raise ValueError(f"Snapshot with reason '{self.reason}' must have a session reference")

    # Non-session snapshots should NOT have a session reference
    if self.reason == InventorySnapshotReason.FORECAST and self.inventory_count_session_key is not None:
      raise ValueError("Forecast snapshots should not have a session reference")

    return self


class InventorySnapshotItem(ArangoDocument): # edge collection
  product_key: str = Field(..., alias='_from')
  position_key: str = Field(..., alias='_to')
  inventory_snapshot_key: str
  quantity: float
  value: float | None = None
  serial_keys: list[str] | None = None
