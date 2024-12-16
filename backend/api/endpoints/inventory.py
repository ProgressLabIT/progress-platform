import traceback
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Depends

from models.inventory import *
from models.product import ProductBaseData
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
    raise HTTPException(
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


@router.get('/position-hierarchy'
#, dependencies=[Depends(auth.verify_token)]
)
def get_position_hierarchy(
  position_key: str | None = None,
):
  try:
    bind_vars = dict(
      position_id = f'Position/{position_key}'
    )
    positions = {}
    starting_positions = set()
    for position in [e for e in db.aql.execute(Queries.GET_POSITION_HIERARCHY, bind_vars=bind_vars)]:
      positions[position['position_id']] = position
      if position['to'] == 'Position/IN':
        starting_positions.add(position['to'])

    #for position in positions:
    #  if positions[position]['from'] != 'Position/IN':
    #    starting_positions.discard(positions[position]['from'])

    position_hierarchy = []
    for starting_position in starting_positions:
      if (starting_position in positions):
         position_children = []
         if (not 'deleted' in positions[starting_position] or not positions[starting_position]['deleted'] == True):
           position_children = get_children(position_key=starting_position, positions=positions, level=0)
         merged_position = dict()
         merged_position.update(positions[starting_position])
         if (len(position_children)>0):
           merged_position['children'] = position_children
         position_hierarchy.append(merged_position)

    filtered_hierarchy = []
    for hierarchy in position_hierarchy:
      if (hierarchy['position_key'] == position_key):
        filtered_hierarchy.append(hierarchy)
      elif ('children' in hierarchy and search_children(position_key, hierarchy['children'])):
          filtered_hierarchy.append(hierarchy)

    return filtered_hierarchy

  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching positions hierarcy from the db.",
        error=traceback.format_exc()
      )
    )

def get_children(position_key, positions, level):
  children = []
  if level > 15:
    return children
  level += 1
  for position in positions:
    if positions[position]['to'] == position_key:
      child_key = positions[position]['from']
      merged_position = dict()
      merged_position.update(positions[child_key])
      position_children = []
      if (not 'deleted' in positions[position] or not positions[position]['deleted'] == True):
        position_children = get_children(position_key=child_key, positions=positions, level=level)
      if (len(position_children)>0):
        merged_position['children'] = position_children
      children.append(merged_position)

  return children

def search_children(position_key, children):
  found = False
  for child in children:
    if (child['position_key'] == position_key):
      found = True
    elif 'children' in child:
      found = found or search_children(position_key, child['children'])
  return found

@router.post('/position',
    dependencies=[Depends(auth.verify_token)])
async def create_position(new_position: PositionNew):

  tx = db.begin_transaction(write=['Position', 'Counter', 'is_in_position'], read=['Config', 'Position'])

  try:
    if not new_position.code:
      positions_counter_key = tx.collection('Config').get('system_counters')['positions']
      new_position.code = _generate_counter(tx, counter_key=positions_counter_key)

    created_position = tx.collection('Position').insert(
      dict(code=new_position.code,
           owned=new_position.owned,
           available=new_position.available,
           disposable=new_position.disposable,
           extra=new_position.extra), return_new=True)
    new_position_key = created_position['_key']

    tx.collection('is_in_position').insert(dict(
                   _from=f'Position/{new_position_key}',
                   _to=f'Position/{new_position.parent_position_key}'
                ))
    tx.commit_transaction()
    return APIResponse(
      status=201,
      message=f"Position {new_position.code} created successfully.",
      detail=created_position['new']
    )
  except Exception as e:
    tx.abort_transaction()
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc(),
    )


@router.patch('/position/{positions_key}',
    dependencies=[Depends(auth.verify_token)])
async def update_position(position_key: str, updated_fields: dict, parent_position_key: str | None = None):

  tx = db.begin_transaction(write=['Position', 'is_in_position'], read=['Config', 'Position'])

  try:
    updated_position = tx.collection('Position').update(
      dict(
        _key=position_key,
        updated=timestamp(),
        **updated_fields
      ), return_new=True
    )['new']

    if (parent_position_key != None):
      link_cursor = tx.collection('is_in_position').find(dict(_from=f'Position/{position_key}'))
      if link_cursor.count()>0:
        tx.collection('is_in_position').update(dict(
          _key = link_cursor.next()['_key'],
          _to=f'Position/{parent_position_key}'))

    tx.commit_transaction()
    response = APIResponse(
      status=200,
      message=f"Position {updated_position['code']} (KEY: {updated_position['_key']}) updated",
      detail=updated_position
    )
    return response
  except Exception as e:
    tx.abort_transaction()
    raise HTTPException(
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

    tx.collection('Position').update(dict(_key=position_key, deleted=True))
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
    return [InventoryMovementSearchResults(**m) for m in results]

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )

@router.get('/movement/latest-receipt-positions',
    dependencies=[Depends(auth.verify_token)])
def get_latest_receipt_positions(limit: int | None = 10):
  try:
    bind_vars = dict(limit= limit)
    results = db.aql.execute(Queries.GET_LATEST_RECEIPT_POSITIONS, bind_vars=bind_vars)
    return [Position(**p) for p in results]

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )

@router.get('/movement/latest-receipt-products',
    dependencies=[Depends(auth.verify_token)])
def get_latest_receipt_products(limit: int | None = 10):
  try:
    bind_vars = dict(limit= limit)
    results = db.aql.execute(Queries.GET_LATEST_RECEIPT_PRODUCTS, bind_vars=bind_vars)
    return [ProductBaseData(**p) for p in results]

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )

#@router.post('/movement',
#    dependencies=[Depends(auth.verify_token)])
#async def create_movements(new_movements: list[InventoryMovement]):
#  try:
#    prepped = [model_to_db_dict(m) for m in new_movements]
#    db.collection('InventoryMovement').insert_many(prepped)
#
#    return APIResponse(message="Positions created successfully")
#  except Exception as e:
#    return HTTPException(
#      status_code=500,
#      detail=traceback.format_exc()
#    )

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


# ===============================================
# INVENTORY
# ===============================================

@router.get('/inventory',
    dependencies=[Depends(auth.verify_token)])
async def get_inventory(params: Annotated[InventorySearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    results = db.aql.execute(Queries.SEARCH_INVENTORY, bind_vars=bind_vars)
    return [InventorySearchResult(**r) for r in results]

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )

@router.get('/inventory/products',
    dependencies=[Depends(auth.verify_token)])
async def get_inventory_products(params: Annotated[InventorySearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    results = db.aql.execute(Queries.SEARCH_INVENTORY_PRODUCT, bind_vars=bind_vars)
    return [ProductBaseData(**r) for r in results]

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )

@router.get('/inventory/positions',
    dependencies=[Depends(auth.verify_token)])
async def get_inventory_positions(params: Annotated[InventorySearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    results = db.aql.execute(Queries.SEARCH_INVENTORY_POSITIONS, bind_vars=bind_vars)
    return [Position(**r) for r in results]

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )

@router.get('/inventory/serials',
    dependencies=[Depends(auth.verify_token)])
async def get_inventory_serials(params: Annotated[InventorySearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    results = db.aql.execute(Queries.SEARCH_INVENTORY_SERIALS, bind_vars=bind_vars)
    return [r for r in results]

  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )




