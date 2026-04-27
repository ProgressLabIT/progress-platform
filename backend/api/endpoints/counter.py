import traceback

from fastapi import APIRouter, HTTPException, Query, Depends

from utils.api import APIResponse
from models.counter import Counter
from utils.db import db
from utils import auth

router = APIRouter()


@router.post('/counter',
    dependencies=[Depends(auth.verify_token)])
def create_counter(counter_data: Counter):
  try:
    counter_key = db.collection('Counter').insert(counter_data)['_key']
    return APIResponse(
      message = "Counter created successfully",
      detail = dict(counter_key=counter_key)
    )
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get('/counter',
    dependencies=[Depends(auth.verify_token)])
def fetch_counter(name: str | None = None, key: str | None = None):
  match = dict()
  if name:
    match['name'] = name
  if key:
    match['_key'] = key
  try:
    cursor = db.collection('Counter').find(match)
    result = [Counter(**f) for f in cursor]
    return sorted(result, key=lambda x: x.name.lower())
  except:
      raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.put('/counter/{counter_key}',
    dependencies=[Depends(auth.verify_token)])
def replace_field_metadata(counter_key: str, counter_data: Counter):
  """Counter data must contain _key"""
  try:
    db.collection('Counter').update(counter_data.dict(by_alias=True), check_rev=False)
    return APIResponse(message = "Counter updated successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.delete('/counter/{counter_key}',
    dependencies=[Depends(auth.verify_token)])
def delete_field(counter_key: str):
  """Delete custom counter"""
  system_counters = db.collection('Config').get('system_counters') or {}
  assigned_slots = [
    slot for slot, key in system_counters.items()
    if slot not in ('_key', '_id', '_rev') and key == counter_key
  ]
  if assigned_slots:
    raise HTTPException(
      status_code=409,
      detail={
        'code': 'counter_in_use_as_system_counter',
        'slots': assigned_slots,
      },
    )

  product_usage = next(db.aql.execute(
    """
    LET refs = (
      FOR p IN Product
        FILTER p.counter_key == @counter_key
        RETURN { _key: p._key, code: p.code, name: p.name }
    )
    RETURN { total: LENGTH(refs), sample: SLICE(refs, 0, 5) }
    """,
    bind_vars={'counter_key': counter_key},
  ))
  if product_usage['total'] > 0:
    raise HTTPException(
      status_code=409,
      detail={
        'code': 'counter_in_use_by_products',
        'total': product_usage['total'],
        'sample': product_usage['sample'],
      },
    )

  try:
    db.collection('Counter').delete(counter_key, return_old=True)['old']
    return APIResponse(message = "Counter successfully deleted")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())
