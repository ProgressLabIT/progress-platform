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
  search: WildcardString = None
  position_keys: list[str] | None = None
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
