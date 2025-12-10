from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from utils.search import WildcardString


# ========================================================
# INVENTORY
# ========================================================

class Inventory(BaseModel): # edge is_in_position
  model_config = ConfigDict(populate_by_name=True)

  key: str | None = Field(None, alias='_key')
  product_id: str = Field(..., alias='_from')
  position_id: str = Field(..., alias='_to')
  serial_key: str | None = None
  quantity: float
  owned: bool = True # False means it's property of customers or suppliers

  counting: bool = False # True means the inventory is being counted
  count_by: str | None = None # inventory count key or other entity counting the inventory (e.g. inventory count session)
  last_counted: datetime | None = None

  value: float | None = None
  extra: Any = None

class InventoryPathItem(BaseModel):
  position_key: str | None = None
  position_code: str | None = None

class InventorySearchResult(BaseModel):
  key: str = Field(..., alias='_key') # Inventory record (is_in_position edge) key
  product_code: str | None = None
  product_description: str | None = None
  position_code: str | None = None
  path: list[InventoryPathItem] | None = []
  serial_code: str | None = None
  serial_key: str | None = None
  product_key: str | None = None
  position_key: str | None = None
  quantity: float
  owned: bool | None = True
  value: float | None = None
  reference: str | None = None
  extra: Any = None


class InventoryGraphSearchParams(BaseModel):
  root_position_key: str | None = None
  product_key: str | None = None
  product_search: WildcardString = None
  serials_only: bool | None = False
  serial_search: WildcardString = None
  serial_keys: list[str] | None = None
  position_search: WildcardString = None
  position_key: str | None = None
  owned: bool | None = None
  limit: int | None = 200
  offset: int | None = 0

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


