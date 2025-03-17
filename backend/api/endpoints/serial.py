import traceback
import json

from base64 import b64decode
from fastapi import APIRouter, HTTPException, Query, Depends
from utils import auth
from datetime import datetime
from typing import Dict, List, Union

from models.form import CustomField
from models.serial import SerialSelection, Serial
from utils.db import db
from utils.bom import get_bom_from_db
from utils.serial import Queries, get_children, get_bom_components_requiring_traceability, search_children

router = APIRouter()

@router.get('/serial-field',
    dependencies=[Depends(auth.verify_token)])
def fetch_field():
  serial_fields = db.collection('Config').get('serial_fields')
  fields = []
  if serial_fields is not None:
    fields = serial_fields['value']
  return fields

@router.get('/serial-batch',
    dependencies=[Depends(auth.verify_token)])
def get_serial_batch(
  batch_key: str | None = None,
  filter_empty: bool = False
):
  bind_vars = dict(batch_key = batch_key)
  batch_serials = []
  for serial in [e for e in db.aql.execute(Queries.GET_ALL_SERIALS_IN_BATCH, bind_vars=bind_vars)]:
    if serial['code'] or not filter_empty:
      batch_serials.append(serial)
  return batch_serials

@router.get('/component-batch',
    dependencies=[Depends(auth.verify_token)])
def get_serial_batch(batch_key: str | None = None):
  bind_vars = dict(
    from_id = f'Batch/{batch_key}'
  )
  return [e for e in db.aql.execute(Queries.GET_ALL_COMPONENTS_IN_BATCH, bind_vars=bind_vars)]

@router.get('/serial-parents',
    dependencies=[Depends(auth.verify_token)])
def get_serial_parents(
  serial_key: str | None = None,
):
  try:
    bind_vars = dict(
      serial_id = f'Serial/{serial_key}'
    )
    cursor = db.aql.execute(Queries.GET_SERIAL_PARENTS, bind_vars=bind_vars)
    parents = [i for i in cursor]
    return parents[::-1]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials hierarcy from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/serial-children',
    dependencies=[Depends(auth.verify_token)])
def get_serial_children(
  serial_key: str | None = None,
):
  try:
    bind_vars = dict(
      serial_id = f'Serial/{serial_key}',
      level = 1
    )
    cursor = db.aql.execute(Queries.GET_SERIAL_CHILDREN, bind_vars=bind_vars)
    return [i for i in cursor]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials hierarcy from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/serial-hierarchy', dependencies=[Depends(auth.verify_token)])
def get_serial_hierarchy(
  serial_key: str | None = None,
  include_expected_components: bool = True,
):
  try:
    bind_vars = dict(
      serial_id = f'Serial/{serial_key}'
    )
    serials = {}
    starting_serials = set()
    for serial in [e for e in db.aql.execute(Queries.GET_SERIAL_HIERARCHY, bind_vars=bind_vars)]:
      serials[serial['serial_id']] = serial
      if serial['from'] != None:
        starting_serials.add(serial['from'])

    for serial in serials:
      if serials[serial]['to'] != None:
        starting_serials.discard(serials[serial]['to'])

    serial_hierarchy = []
    for starting_serial in starting_serials:
      if (starting_serial in serials):
         serial_children = []
         if (not serials[starting_serial]['replaced'] == True):
           serial_children = get_children(serial_key=starting_serial, serials=serials, level=0, include_expected=include_expected_components, db=db)
         merged_serial = dict()
         merged_serial.update(serials[starting_serial])
         if (len(serial_children)>0):
           merged_serial['children'] = serial_children
         serial_hierarchy.append(merged_serial)

    filtered_hierarchy = []
    for hierarchy in serial_hierarchy:
      if (hierarchy['serial_key'] == serial_key):
        filtered_hierarchy.append(hierarchy)
      elif ('children' in hierarchy and search_children(serial_key, hierarchy['children'])):
          filtered_hierarchy.append(hierarchy)

    return filtered_hierarchy

  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials hierarcy from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/wip-serial',
    dependencies=[Depends(auth.verify_token)])
def get_serial_wip(
  wo_key: str | None = None,
  job_key: str | None = None,
  phase_key: str | None = None,
):
  bind_vars = dict(
    wo_key = wo_key,
    phase_key = phase_key,
    job_key = job_key
  )
  cursor = db.aql.execute(Queries.GET_AVAILABLE_WIP_SERIALS, bind_vars=bind_vars)
  return [SerialSelection(**s) for s in cursor]

@router.get('/serial-selection',
    dependencies=[Depends(auth.verify_token)])
def get_serial_selection(
  search: str | None = None,
  wo_key: str | None = None,
  product_key: str | None = None,
  batch_key: str | None = None,
  filter_used: bool = False,
  include_unreleased: bool = False,
  limit: int = 100
):
  return [e for e in db.aql.execute(Queries.GET_ALL_SERIALS, bind_vars=dict(
      search = search,
      wo_key = wo_key,
      product_key = product_key,
      batch_key = batch_key,
      limit = limit,
      filter_used = filter_used,
      include_unreleased = include_unreleased
    ))]


# ---------------------------------------------
# SERIALS
# ---------------------------------------------

@router.get('/serial/{serial_key}',
    dependencies=[Depends(auth.verify_token)])
def get_serial_from_key(serial_key: str):
  try:
    return db.collection('Serial').get(serial_key)
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/serial-code',
    dependencies=[Depends(auth.verify_token)])
def get_serial_from_code(serial_code: str | None = None,
                         product_key: str | None = None):
  bind_vars = dict(
    serial_code = serial_code,
    product_key = product_key
  )
  try:
    cursor = db.aql.execute(Queries.GET_SERIALS_FOR_CODE, bind_vars=bind_vars)
    return [i for i in cursor]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/serial-code/verify-free',
    dependencies=[Depends(auth.verify_token)])
def verify_serial_code_free(serial_code: str | None = None,
                         product_key: str | None = None,
                         serial_key: str | None = None):
   cursor = db.aql.execute(
     Queries.GET_SERIALS_FOR_SERIAL_CODE,
          bind_vars=dict(
            serial_key=serial_key,
            serial=serial_code,
            product_key=product_key
          )
        )
   try:
    return len([Serial(**t) for t in cursor])<=0
   except:
     return False

@router.get('/serial',
    dependencies=[Depends(auth.verify_token)])
async def search_serials(
  serial_key: Union[List[str], None] = Query(default=None),
  serial_search: str | None = None,
  is_contained_in: str | None = None,
  contains: str | None = None,
  time_created_from: datetime | None = None,
  time_created_to: datetime | None = None,
  created_by: Union[List[str], None] = Query(default=None),
  advanced_filters: str = Query(default=None),
  product_key: Union[List[str], None] = Query(default=None),
  product_code_search: str | None = None,
  work_order_search: str | None = None,
  limit: int | None = 200,
  serial_deleted: bool = False,
  offset: int | None = None,
  filter_unreleased: bool = False,
  sort_by: str | None = 'created',
  sorting_order: str | None = 'desc',
  ):

  serial_fields = db.collection('Config').get('serial_fields')
  fields = []
  if serial_fields is not None:
    fields = serial_fields['value']
  # use query parameters to filter specific type
  bind_vars = dict(
    serial_key = serial_key,
    serial_search = serial_search,
    time_created_from = time_created_from,
    time_created_to = time_created_to,
    created_by = created_by,
    product_key = product_key,
    product_code_search = product_code_search,
    is_contained_in = is_contained_in,
    contains = contains,
    work_order_search = work_order_search,
    filter_unreleased = filter_unreleased,
    advanced_filters = json.loads(b64decode(advanced_filters).decode('latin-1')) if advanced_filters else None,
    limit = limit,
    offset = offset,
    deleted = serial_deleted,
    fields = fields,
    sort_by = sort_by,
    sorting_order = sorting_order
  )
  try:
    cursor = db.aql.execute(Queries.FIND_SERIALS, bind_vars=bind_vars)
    return [i for i in cursor]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/wo-serials',
    dependencies=[Depends(auth.verify_token)])
async def search_wo_serials(
  work_order_key: str | None = None,
  ):
  bind_vars = dict(
    work_order_key = work_order_key
  )
  try:
    work_order_data = db.collection('WorkOrder').get(work_order_key)
    if (work_order_data['traceability_level'] != None):
      return [i for i in db.aql.execute(Queries.FIND_WO_SERIALS, bind_vars=bind_vars)]
    else:
      return [i for i in db.aql.execute(Queries.FIND_WO_BATCH, bind_vars=bind_vars)]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials from the db.",
        error=traceback.format_exc()
      )
    )
