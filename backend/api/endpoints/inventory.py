import traceback
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Depends

from models.inventory import *
from utils.api import APIResponse
from utils.inventory import Queries
from utils.counter import _generate_counter
from utils.db import db, model_to_db_dict
from utils import auth

router = APIRouter()

# ===============================================
# POSITIONS
# ===============================================

@router.get('/position',
    dependencies=[Depends(auth.verify_token)])
async def get_positions(params: Annotated[PositionSearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    results = db.aql.execute(Queries.SEARCH_POSITIONS, bind_vars=bind_vars)
    return [Position(**r) for r in results]

  except Exception as e:
    return HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )



@router.get('/position/{position_key}',
    dependencies=[Depends(auth.verify_token)])
async def get_position_contents(position_key):
  try:
    return db.collection('Position').get(position_key)
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching position from the db.",
        error=traceback.format_exc()
      )
    )



@router.post('/position',
    dependencies=[Depends(auth.verify_token)])
async def create_position(new_position: Position, parent_position_key: str | None = 'IN'):

  tx = db.begin_transaction(write=['Position', 'Counter', 'is_in_position'], read=['Config', 'Position'])

  try:
    if not new_position.code:
      positions_counter_key = tx.collection('Config').get('system_counters')['positions']
      new_position.code = _generate_counter(tx, counter_key=positions_counter_key)

    new_position_key = tx.collection('Position').insert(new_position, return_new=True)['_key']

    tx.collection('is_in_position').insert(dict(
                   _from=f'Position/{new_position_key}',
                   _to=f'Position/{parent_position_key}'
                ))
    tx.commit_transaction()
    return APIResponse(
      status=201,
      message=f"Position {new_position.code} created successfully."
    )
  except Exception as e:
    tx.abort_transaction()
    return HTTPException(
      status_code=500,
      detail=traceback.format_exc(),
    )


@router.delete('/position/{position_key}',
    dependencies=[Depends(auth.verify_token)])
async def delete_position(position_key):
  if position_key == 'IN':
    raise HTTPException(status_code=500, detail='Cannot delete default position')

  try:
    tx = db.begin_transaction(write=['Position', 'is_in_position'])

    cursor = tx.aql.execute(Queries.GET_POSITION_CHILDREN_COUNT, bind_vars=dict(is_in_position = position_key))
    if cursor.next() > 0:
      tx.abort_transaction();
      raise HTTPException(status_code=500, detail='Cannot delete position with children')

    tx.collection('Position').delete(position_key)
    tx.collection('is_in_position').delete_match(filters=dict(_from=f'Position/{position_key}'))

    tx.commit_transaction()

    return APIResponse(message = "Position deleted successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



# ===============================================
# MOVEMENTS
# ===============================================

@router.get('/movement',
    dependencies=[Depends(auth.verify_token)])
def search_inventory_journal(params: Annotated[InventoryMovementSearchParameters, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    results = db.aql.execute(Queries.SEARCH_MOVEMENTS, bind_vars=bind_vars)
    return [InventoryMovement(**m) for m in results]

  except Exception as e:
    return HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )


@router.post('/movement',
    dependencies=[Depends(auth.verify_token)])
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

@router.get('/mission',
    dependencies=[Depends(auth.verify_token)])
async def search_warehouse_missions(
  search: str | None = None, # searches the mission code and references
  includes_product_key: str | None = None,
  includes_product_code: str | None = None,
  due_by_min: date | None = None,
  due_by_max: date | None = None,
  status: MovementStatus | None = None,
):
  ...


@router.get('/mission/{mission_key}',
    dependencies=[Depends(auth.verify_token)])
def get_warehouse_mission_details(mission_key):
  # Must include data about all the related movements
  ...



