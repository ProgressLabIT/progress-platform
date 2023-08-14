import traceback

from fastapi import APIRouter, HTTPException, Query

from utils.api import APIResponse
from models.form import CustomField, CustomListValue
from utils.db import db, model_to_db_dict

router = APIRouter()


@router.post('/field')
def create_field(field_data: CustomField):
  try:
    field_key = db.collection('CustomField').insert(field_data)['_key']
    return APIResponse(
      message = "Field created successfully",
      detail = dict(field_key=field_key)
    )
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get('/field')
def fetch_field(name: str = None, key: str = None):
  match = dict()
  if name:
    match['name'] = name
  if key:
    match['_key'] = key

  cursor = db.collection('CustomField').find(match)
  result = [CustomField(**f) for f in cursor]
  return sorted(result, key=lambda x: x.name.lower())



@router.put('/field/{field_key}')
def update_field(field_key: str, field_data: CustomField):
  """Field data must contain _key"""
  try:
    db.collection('CustomField').update(field_data.dict(by_alias=True), check_rev=False)
    return APIResponse(message = "Field updated successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.get('/list')
def fetch_custom_list_values(field_key: str):
  match = dict(field_key=field_key)
  cursor = db.collection('CustomListValue').find(match)
  result = [CustomListValue(**v) for v in cursor]
  return sorted(result, key=lambda x: x.value)


@router.post('/list/{field_key}')
def create_or_update_custom_list_values(
  field_key: str,
  new_values: list[CustomListValue],
  reset: bool = False
  ):
  try:
    tx = db.begin_transaction(write=['CustomListValue'])
    collection = tx.collection('CustomListValue')

    if reset:
      collection.delete_match(dict(field_key=field_key))

    # The current version of the python-arango client ignores the custom serializer when doing bulk operations, must use it explicitly here
    prepped = [model_to_db_dict(l) for l in new_values]
    collection.insert_many(prepped, overwrite=True)
    tx.commit_transaction()
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())

@router.delete('/list/{field_key}')
def delete_custom_list_value(
  field_key: str,
  value_key: list[str] = Query(...)
  ):
  db.collection('CustomListValue').delete_many(value_key, check_rev=False)
