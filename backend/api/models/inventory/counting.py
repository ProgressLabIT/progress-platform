from datetime import datetime
from enum import Enum
from typing import Any


from pydantic import Field, model_validator

from models.base_models import ArangoDocument
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
  BY_POSITION = 'position'
  BY_PRODUCT = 'product'

class InventoryCountSession(ArangoDocument):
  code: str  # Auto-generated from counter
  description: str | None = None
  type: InventoryCountSessionType
  status: InventoryCountSessionStatus = InventoryCountSessionStatus.PLANNED
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


class InventoryCountAssignment(ArangoDocument):
  inventory_count_session_key: str  # Parent campaign

  # What was assigned
  assignment_type: InventoryCountSessionType  # What was assigned
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
  SUBMITTED = 'submitted'
  CONFIRMED = 'confirmed'
  DISCARDED = 'discarded'

class InventoryCountRecord(ArangoDocument):
  # What was counted
  product_key: str
  position_key: str
  serial_keys: list[str] | None = None

  # Core data
  system_qt: float  # Snapshot at count time. Must be retaken in case count is updated before submission
  system_at: datetime | None = None

  counted_qt: float
  counted_at: datetime | None = None

  # Metadata
  inventory_count_session_key: str
  assignment_key: str | None = None
  status: InventoryCountStatus = InventoryCountStatus.DRAFT
  reviewed_at: datetime | None = None # Either confirmed or discarded
  notes: str | None = None
  extra: Any = None

  @property
  def product_id(self) -> str:
    return f'Product/{self.product_key}'

  @property
  def position_id(self) -> str:
    return f'Position/{self.position_key}'

  @property
  def delta(self) -> float | None:
    return self.counted_qt - self.system_qt


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
