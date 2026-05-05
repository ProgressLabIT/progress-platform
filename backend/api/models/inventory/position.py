from datetime import datetime
from enum import Enum
from typing import Any


from pydantic import BaseModel, Field

from models.base_models import ArangoDocument, ArangoEdge, FlexModel
#from utils.counter import _generate_counter
from utils.dt import timestamp
from utils.search import WildcardString

# ========================================================
# POSITIONS
# ========================================================

class Position(ArangoDocument):
  code: str | None = Field(None, description="Human-readable position code shown in the warehouse UI.", examples=["WAREHOUSE-A", "LOCATION-A1-01"])
  owned: bool | None = Field(True, description="True if this position belongs to the company (not a customer or supplier).", examples=[True])
  available: bool | None = Field(True, description="True if the position is available for movements.", examples=[True])
  disposable: bool | None = Field(False, description="If True, the position is automatically deleted when emptied or shipped.", examples=[False])
  fixed: bool | None = Field(True, description="True for fixed warehouse locations; False for mobile carriers (e.g. trolleys).", examples=[True])
  deleted: bool | None = Field(False, description="Soft-delete flag; True means the position has been logically removed.", examples=[False])
  created: datetime | None = Field(default_factory=timestamp, description="Timestamp when the position was created.", examples=["2026-05-15T10:00:00Z"])
  allow_consumption: bool | None = Field(None, description="Override flag: if set, enables or disables consumption movements from this position regardless of global policy.", examples=[None])
  extra: Any = Field(None, description="Arbitrary extra metadata stored alongside the position document.", examples=[None])

class PositionNew(FlexModel):
  parent_position_key: str | None = Field('IN', description="Key of the parent position in the warehouse hierarchy. Defaults to the root `IN` position.", examples=["IN", "12345"])
  code: str | None = Field(None, description="Position code; auto-generated from the system counter if omitted.", examples=["LOCATION-A1-01"])
  owned: bool | None = Field(True, description="True if this position is owned by the company.", examples=[True])
  available: bool | None = Field(True, description="True if the position accepts movements on creation.", examples=[True])
  fixed: bool | None = Field(True, description="True for fixed locations; False for mobile carriers.", examples=[True])
  disposable: bool | None = Field(False, description="If True, the position is auto-deleted when emptied.", examples=[False])
  allow_consumption: bool | None = Field(None, description="Override consumption policy for this position.", examples=[None])
  extra: Any = Field(None, description="Arbitrary extra metadata.", examples=[None])



class PositionType(str, Enum):
  FROM = 'from'
  TO = 'to'

class PositionLink(ArangoEdge):  #edge is_in_position
 """
 the is_in_position collection is used both for inventory and for position hierarchy.
 This class is only used to distinguish what we're using the collection for.
 """
 pass


class PositionSearchParams(BaseModel):
  search: WildcardString = Field(None, description="Wildcard search against position code.", examples=["WAREHOUSE-A*"])
  position_keys: list[str] | None = Field(None, description="Filter to positions with these specific keys.", examples=[["12345", "67890"]])
  has_product_key: list[str] | None = Field(None, description="Return only positions that currently contain at least one unit of these products.", examples=[["product/67890"]])
  has_product_code: list[str] | None = Field(None, description="Return only positions containing products whose code matches any of the given values.", examples=[["PROD-001"]])
  is_in_position: str | None = Field(None, description="Filter to positions that are children of this position key in the hierarchy.", examples=["IN"])
  contains_position: str | None = Field(None, description="Filter to positions that contain this child position key.", examples=["12345"])
  fixed_only: bool | None = Field(False, description="If True, return only fixed (non-mobile) positions.", examples=[False])
  limit: int | None = Field(200, description="Maximum number of results to return.", examples=[200])
  offset: int | None = Field(0, description="Number of results to skip for pagination.", examples=[0])
