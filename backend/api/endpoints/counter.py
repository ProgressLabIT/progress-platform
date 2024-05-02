import traceback

from fastapi import APIRouter, HTTPException, Query

from utils.api import APIResponse
from models.counter import Counter
from utils.db import db

router = APIRouter()


@router.post('/counter')
def create_counter(counter_data: Counter):
  try:
    counter_key = db.collection('Counter').insert(counter_data)['_key']
    return APIResponse(
      message = "Counter created successfully",
      detail = dict(counter_key=counter_key)
    )
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get('/counter')
def fetch_counter(name: str | None = None, key: str | None = None):
  match = dict()
  if name:
    match['name'] = name
  if key:
    match['_key'] = key

  cursor = db.collection('Counter').find(match)
  result = [Counter(**f) for f in cursor]
  return sorted(result, key=lambda x: x.name.lower())



@router.put('/counter/{counter_key}')
def replace_field_metadata(counter_key: str, counter_data: Counter):
  """Counter data must contain _key"""
  try:
    db.collection('Counter').update(counter_key.dict(by_alias=True), check_rev=False)
    return APIResponse(message = "Counter updated successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.delete('/counter/{counter_key}')
def delete_field(counter_key: str):
  """Delete custom counter"""
  try:
    db.collection('Counter').delete(counter_key, return_old=True)['old']
    return APIResponse(message = "Counter successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())
