import traceback
import json

from base64 import b64decode
from fastapi import APIRouter, HTTPException, Query, Depends
from utils import auth
from datetime import datetime
from typing import Dict, List, Union

from commons.models.form import CustomField
from commons.utils.db import db

from commons.utils.serial import Queries

router = APIRouter()

@router.get('/serial-field',
    dependencies=[Depends(auth.verify_token)])
def fetch_field():
  serial_fields = db.collection('Config').get('serial_fields')
  fields = []
  if serial_fields is not None:
    fields = serial_fields['value']
  return fields


@router.get('/product-steps/{product_key}',
    dependencies=[Depends(auth.verify_token)])
def get_product_steps(product_key: str):
  bind_vars = dict(
    product_key = product_key
  )
  return [e for e in db.aql.execute(Queries.GET_PRODUCT_STEPS, bind_vars=bind_vars)]

@router.get('/serial-batch',
    dependencies=[Depends(auth.verify_token)])
def get_serial_batch(
  wo_key: str | None = None,
  job_key: str | None = None,
):
  bind_vars = dict(
    wo_key = wo_key,
    job_key = f'Job/{job_key}'
  )
  return [e for e in db.aql.execute(Queries.GET_SERIALS_IN_BATCH, bind_vars=bind_vars)]


@router.get('/serial-wo-phase',
    dependencies=[Depends(auth.verify_token)])
def get_serial_wo_phase(
  wo_key: str | None = None,
  phase_key: str | None = None,
):
  bind_vars = dict(
    wo_key = wo_key,
    phase_key = f'Phase/{phase_key}'
  )
  wo_serials = []
  for serial in [e for e in db.aql.execute(Queries.GET_AVAILABLE_SERIALS_IN_WORK_ORDER, bind_vars=bind_vars)]:
    if serial['code']:
      wo_serials.append(dict(
          serial_key= serial['_key'],
          serial_code= serial['code'],
          active= serial['active'],
      ))
    else:
      wo_serials.append(dict(
          serial_key= serial['_key'],
          serial_code= serial['_key'],
          active= serial['active'],
      ))
  return wo_serials

@router.get('/serial-selection',
    dependencies=[Depends(auth.verify_token)])
def get_serial_selection(
  search: str | None = None,
  wo_key: str | None = None,
  product_key: str | None = None,
  limit: int = 100
):
  all_serials = []
  for serial in [e for e in db.aql.execute(Queries.GET_ALL_SERIALS, bind_vars=dict(
      search = search,
      wo_key = wo_key,
      product_key = product_key,
      limit = limit
    ))]:
    if serial['code']:
      all_serials.append(dict(
          value= serial['_key'],
          _key= serial['_key'],
          label= serial['code'],
          wo_key= serial['wo_key'],
          product_key= serial['product_key'],
      ))
  return all_serials


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


@router.get('/serial',
    dependencies=[Depends(auth.verify_token)])
async def search_serials(
  serial_key: Union[List[str], None] = Query(default=None),
  serial_search: str | None = None,
  time_created_from: datetime | None = None,
  time_created_to: datetime | None = None,
  created_by: Union[List[str], None] = Query(default=None),
  advanced_filters: str = Query(default=None),
  product_key: Union[List[str], None] = Query(default=None),
  product_code_search: str | None = None,
  work_order_search: str | None = None,
  limit: int | None = None,
  serial_deleted: bool = False,
  offset: int | None = None,
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
    work_order_search = work_order_search,
    advanced_filters = json.loads(b64decode(advanced_filters).decode('latin-1')) if advanced_filters else None,
    limit = limit,
    offset = offset,
    deleted = serial_deleted,
    fields = fields
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


