from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from utils.search import WildcardString


# ========================================================
# INVENTORY
# ========================================================

class Inventory(BaseModel): # edge is_in_position
  model_config = ConfigDict(populate_by_name=True)

  key: str | None = Field(None, alias='_key', description="ArangoDB document key for the `is_in_position` edge record.", examples=["inv-edge-001"])
  product_id: str = Field(..., alias='_from', description="ArangoDB document ID of the product (`Product/<key>`).", examples=["Product/67890"])
  position_id: str = Field(..., alias='_to', description="ArangoDB document ID of the position (`Position/<key>`).", examples=["Position/12345"])
  serial_key: str | None = Field(None, description="Key of the serial number tracked in this inventory slot, if applicable.", examples=["SN-LR-001234"])
  quantity: float = Field(..., description="Quantity of the product currently at this position.", examples=[100.0])
  owned: bool = Field(True, description="False if this inventory belongs to a customer or supplier (consignment stock).", examples=[True])

  counting: bool = Field(False, description="True while the inventory record is being counted in an active counting session.", examples=[False])
  count_by: str | None = Field(None, description="Key of the entity (e.g. `InventoryCountSession/<key>`) that is currently counting this inventory.", examples=["InventoryCountSession/abc123"])
  last_counted: datetime | None = Field(None, description="Timestamp of the last completed count for this inventory record.", examples=["2026-04-01T08:30:00Z"])

  locked: bool = Field(False, description="True while the inventory is locked for adjustment processing (prevents concurrent movements).", examples=[False])
  locked_by: str | None = Field(None, description="Key of the count session that has locked this inventory record.", examples=["InventoryCountSession/abc123"])

  value: float | None = Field(None, description="Monetary value of the inventory at this position.", examples=[2500.0])
  extra: Any = Field(None, description="Arbitrary extra metadata.", examples=[None])

class InventoryPathItem(BaseModel):
  position_key: str | None = Field(None, description="Key of a position in the path from root to the current position.", examples=["12345"])
  position_code: str | None = Field(None, description="Human-readable code of the position in the path.", examples=["WAREHOUSE-A"])

class InventorySearchResult(BaseModel):
  key: str = Field(..., alias='_key', description="Key of the `is_in_position` edge (inventory record).", examples=["inv-edge-001"])
  product_code: str | None = Field(None, description="Code of the product at this inventory slot.", examples=["PROD-001"])
  product_description: str | None = Field(None, description="Description of the product.", examples=["Steel bracket M6"])
  position_code: str | None = Field(None, description="Code of the storage position.", examples=["LOCATION-A1-01"])
  path: list[InventoryPathItem] | None = Field([], description="Path of positions from the warehouse root to this position.", examples=[[]])
  serial_code: str | None = Field(None, description="Serial number code if this is a serialized inventory slot.", examples=["SN-LR-001234"])
  serial_key: str | None = Field(None, description="Key of the serial document.", examples=["SN-LR-001234"])
  product_key: str | None = Field(None, description="Key of the product document.", examples=["67890"])
  position_key: str | None = Field(None, description="Key of the position document.", examples=["12345"])
  quantity: float = Field(..., description="Quantity held at this position.", examples=[42.5])
  owned: bool | None = Field(True, description="False if this is consignment stock.", examples=[True])
  value: float | None = Field(None, description="Monetary value of this inventory slot.", examples=[1062.5])
  reference: str | None = Field(None, description="External reference associated with this inventory slot.", examples=["WO-2026-001"])
  extra: Any = Field(None, description="Arbitrary extra metadata.", examples=[None])


class InventoryGraphSearchParams(BaseModel):
  root_position_key: str | None = Field(None, description="Traverse the position graph starting from this position key; omit to search the entire warehouse.", examples=["IN"])
  product_key: str | None = Field(None, description="Filter to inventory slots containing this product.", examples=["67890"])
  product_search: WildcardString = Field(None, description="Wildcard search on product code.", examples=["PROD-*"])
  serials_only: bool | None = Field(False, description="If True, return only serialized inventory slots.", examples=[False])
  serial_search: WildcardString = Field(None, description="Wildcard search on serial code.", examples=["SN-LR-*"])
  serial_keys: list[str] | None = Field(None, description="Filter to inventory slots containing any of these serial keys.", examples=[["SN-LR-001234"]])
  position_search: WildcardString = Field(None, description="Wildcard search on position code.", examples=["LOCATION-A*"])
  position_key: str | None = Field(None, description="Filter to this specific position.", examples=["12345"])
  owned: bool | None = Field(None, description="Filter by ownership flag; None returns all.", examples=[True])
  limit: int | None = Field(200, description="Maximum number of results.", examples=[200])
  offset: int | None = Field(0, description="Pagination offset.", examples=[0])

class InventorySearchParams(BaseModel):
  #TODO uncomment
  product_key: str | None = Field(None, description="Filter by product key.", examples=["67890"])
  product_code: str | None = Field(None, description="Filter by exact product code.", examples=["PROD-001"])
  position_key: str | None = Field(None, description="Filter by position key.", examples=["12345"])
  position_code: str | None = Field(None, description="Filter by exact position code.", examples=["LOCATION-A1-01"])
  serial_keys: list[str] | None = Field(None, description="Filter to inventory slots for any of these serial keys.", examples=[["SN-LR-001234"]])
  # serial_code: str | None = None
  owned: bool | None = Field(None, description="Filter by ownership; None returns all.", examples=[None])
  limit: int | None = Field(200, description="Maximum number of results.", examples=[200])
  offset: int | None = Field(0, description="Pagination offset.", examples=[0])
  strict: bool | None = Field(False, description="If True, apply exact-match logic instead of wildcard matching.", examples=[False])
