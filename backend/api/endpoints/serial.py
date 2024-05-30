import traceback
import json

from base64 import b64decode
from fastapi import APIRouter, HTTPException, Query, Request
from utils.api import APIResponse
from datetime import datetime
from typing import Dict, List, Union
from sse_starlette.sse import EventSourceResponse

from commons.models.form import CustomField, CustomListValue, FieldType
from commons.utils.db import db, model_to_db_dict
from utils.server_event_manager import ServerEventManager


from commons.utils.serial import Queries

router = APIRouter()

@router.get('/serial-field')
def fetch_field(name: str | None = None, key: str | None = None):
  match = dict()
  if name:
    match['name'] = name
  if key:
    match['_key'] = key
  match['use_in_serial'] = True
  cursor = db.collection('CustomField').find(match)
  result = [CustomField(**f) for f in cursor]
  return sorted(result, key=lambda x: x.name.lower())


@router.get('/product-steps/{product_key}')
def get_product_steps(product_key: str):
  bind_vars = dict(
    product_key = product_key
  )
  return [e for e in db.aql.execute(Queries.GET_PRODUCT_STEPS, bind_vars=bind_vars)]

@router.get('/serial-batch/{batch_key}')
def get_serial_batch(batch_key: str):
  bind_vars = dict(
    from_id = f'Batch/{batch_key}'
  )
  batch_serials = []
  for serial in [e for e in db.aql.execute(Queries.GET_SERIALS_IN_BATCH, bind_vars=bind_vars)]:
    if serial['serial']:
      batch_serials.append(dict(
          value= serial['key'],
          label= serial['serial'],
      ))
  return batch_serials


@router.get('/serial-wo')
def get_serial_batch(
  wo_key: str | None = None,
  phase_key: str | None = None,
):
  bind_vars = dict(
    wo_key = wo_key,
    phase_key = f'Phase/{phase_key}'
  )
  wo_serials = []
  for serial in [e for e in db.aql.execute(Queries.GET_AVAILABLE_SERIALS_IN_WORK_ORDER, bind_vars=bind_vars)]:
    if serial['serial']:
      wo_serials.append(dict(
          value= serial['key'],
          label= serial['serial'],
      ))
  return wo_serials




# ---------------------------------------------
# SERIALS
# ---------------------------------------------


@router.get('/serial')
async def search_serials(
  serial_key: Union[List[str], None] = Query(default=None),
  serial_key_search: str | None = None,
  time_created_from: datetime | None = None,
  time_created_to: datetime | None = None,
  created_by: Union[List[str], None] = Query(default=None),
  advanced_filters: str = Query(default=None),
  product_key: Union[List[str], None] = Query(default=None),
  product_code_search: str | None = None,
  limit: int | None = None,
  serial_deleted: bool = False
 # with_links: bool = False
  ):
  # use query parameters to filter specific type
  bind_vars = dict(
    serial_key = serial_key,
    serial_key_search = serial_key_search,
    time_created_from = time_created_from,
    time_created_to = time_created_to,
    created_by = created_by,
    product_key = product_key,
    product_code_search = product_code_search,
    advanced_filters = json.loads(b64decode(advanced_filters).decode('latin-1')) if advanced_filters else None,
    limit = limit,
    deleted = serial_deleted
    #with_links = with_links
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

@router.get("/notification")
async def message_stream(request: Request):
    return EventSourceResponse(ServerEventManager.getInstance().push_events(request, 'serial-notification'))

