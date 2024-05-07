import traceback

from fastapi import APIRouter, HTTPException, Query

from utils.api import APIResponse
from commons.models.form import CustomField, CustomListValue, FieldType
from commons.utils.db import db, model_to_db_dict
from utils.serial import Queries
from typing import Dict, List, Union


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




# ---------------------------------------------
# SERIALS
# ---------------------------------------------


@router.get('/serial')
async def search_serials(
  serial_key: Union[List[str], None] = Query(default=None),
  limit: int | None = None,
  with_links: bool = False
  ):
  # use query parameters to filter specific type
  bind_vars = dict(
    serial_key = serial_key,
    limit = limit,
    with_links = with_links
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

