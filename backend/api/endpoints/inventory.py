import traceback

from fastapi import APIRouter, HTTPException, Query, Depends

from models.inventory import *
from utils.api import APIResponse
from utils.inventory import Queries
from utils.counter import _generate_counter
from utils.db import db, model_to_db_dict

router = APIRouter()

# ===============================================
# POSITIONS
# ===============================================

@router.get('/position')
async def get_positions(
  search: str | None = None,
  has_product_key: list[str] | None = None,
  has_product_code: list[str] | None = None,
  is_in_position: str | None = None,
  contains_position: str | None = None,
  limit: int | None = 200,
  offset: int | None = 0
):

  bind_vars = dict(
    search = search,
    has_product_key = has_product_key,
    has_product_code = has_product_code,
    is_in_position = is_in_position,
    contains_position = contains_position,
    limit = limit,
    offset = offset
  )

  try:
    results = db.aql.execute(Queries.SEARCH_POSITIONS, bind_vars=bind_vars)
    return [Position(**r) for r in results]

  except Exception as e:
    return HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )



@router.get('/position/{position_key}')
async def get_position_contents(position_key):
  ...



@router.post('/position')
async def create_position(new_position: Position):

  if not new_position.code:
    positions_counter_key = db.collection('Config').get('system_counters')['positions']
    new_position.code = _generate_counter(db, positions_counter_key)

  try:
    db.collection('Position').insert(new_position)

    return APIResponse(
      status=201,
      message=f"Position {new_position.code} created successfully."
    )
  except Exception as e:
    return HTTPException(
      status_code=500,
      detail=traceback.format_exc(),
    )


@router.delete('/position/{position_key}')
async def delete_position(position_key):
  ...



# ===============================================
# MOVEMENTS
# ===============================================

@router.get('/movement')
def search_inventory_journal(
  movement_type: InventoryMovementType | None = None,
  movement_status: MovementStatus | None = None,
  include_planned: bool | None = False,
  start_from: datetime | None = None,
  start_to: datetime | None = None,
  end_from: datetime | None = None,
  end_to: datetime | None = None,
  product_key: str | None = None,
  product_code: str | None = None,
  serial_key: str | None = None,
  serial_code: str | None = None,
  mission_key: str | None = None,
  mission_code: str | None = None,
  movement_doc: str | None = None,
  through_position_key: str | None = None,
  through_position_code: str | None = None,
  include_child_positions: bool | None = True,
  search_extra: dict | None = None # search extra attributes
):
  ...


@router.post('/movement')
async def create_movements(new_movements: list[InventoryMovement]):
  try:
    prepped = [model_to_db_dict(m) for m in new_movements]
    db.collection('InventoryMovement').insert_many(prepped)

    return APIResponse(message="Positions created successfully")
  except Exception as e:
    return HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )

# ===============================================
# MISSIONS
# ===============================================

@router.get('/mission')
async def search_warehouse_missions(
  search: str | None = None, # searches the mission code and references
  includes_product_key: str | None = None,
  includes_product_code: str | None = None,
  due_by_min: date | None = None,
  due_by_max: date | None = None,
  status: MovementStatus | None = None,
):
  ...


@router.get('/mission/{mission_key}')
def get_warehouse_mission_details(mission_key):
  # Must include data about all the related movements
  ...



