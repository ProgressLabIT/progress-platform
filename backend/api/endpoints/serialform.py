import traceback

from fastapi import APIRouter, HTTPException, Query

from utils.api import APIResponse
from models.form import CustomField, CustomListValue, FieldType
from utils.db import db, model_to_db_dict

router = APIRouter()


@router.post('/serial-field')
def create_field(field_data: CustomField):
  try:
    field_key = db.collection('SerialCustomField').insert(field_data)['_key']
    return APIResponse(
      message = "Serial Field created successfully",
      detail = dict(field_key=field_key)
    )
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get('/serial-field')
def fetch_field(name: str | None = None, key: str | None = None):
  match = dict()
  if name:
    match['name'] = name
  if key:
    match['_key'] = key

  cursor = db.collection('SerialCustomField').find(match)
  result = [CustomField(**f) for f in cursor]
  return sorted(result, key=lambda x: x.name.lower())



@router.put('/serial-field/{field_key}')
def replace_field_metadata(field_key: str, field_data: CustomField):
  """Field data must contain _key"""
  try:
    db.collection('SerialCustomField').update(field_data.dict(by_alias=True), check_rev=False)
    return APIResponse(message = "Serial Field updated successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.delete('/serial-field/{field_key}')
def delete_field(field_key: str):
  """Delete custom serial field and linked list values"""
  try:
    tx = db.begin_transaction(write=['SerialCustomField', 'SerialCustomListValue'])
    deleted = tx.collection('SerialCustomField').delete(field_key, return_old=True)['old']

    # Delete list values
    if CustomField(**deleted).type == FieldType.CHOICE:
      tx.collection('SerialCustomListValue').delete_match(dict(field_key=field_key))

    tx.commit_transaction()

    return APIResponse(message = "Field deleted successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.get('/serial-list')
def fetch_custom_list_values(
  field_key: str,
  limit: int = 100,
  search: str | None = None,
  sort_by: str = 'value'
  ):
  query = """
    FOR v IN SerialCustomListValue
    FILTER
      v.field_key == @field_key
      && (@search ? LOWER(CONCAT(v.value, ' ', v.ext_key)) LIKE CONCAT('%', LOWER(@search), '%') : true)
      // space is added to avoid finding matches valid only with the concatenation (across the two fields)
    SORT v[@sort_by]
    LIMIT @limit
    RETURN v
  """
  cursor = db.aql.execute(query, bind_vars=dict(
    field_key = field_key,
    limit = limit,
    search = search,
    sort_by = sort_by
  ))
  results = [CustomListValue(**v) for v in cursor]
  return results


@router.post('/serial-list/{field_key}')
def create_or_update_custom_list_values(
  field_key: str,
  new_values: list[CustomListValue],
  reset: bool = False
  ):
  try:
    tx = db.begin_transaction(write=['SerialCustomListValue'])
    collection = tx.collection('SerialCustomListValue')

    if reset:
      collection.delete_match(dict(field_key=field_key))

    # The current version of the python-arango client ignores the custom serializer when doing bulk operations, must use it explicitly here
    prepped = [model_to_db_dict(l) for l in new_values]
    collection.insert_many(prepped, overwrite=True)
    tx.commit_transaction()
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())

@router.delete('/serial-list/{field_key}')
def delete_custom_list_value(
  field_key: str,
  value_key: list[str] = Query(...)
  ):
  db.collection('SerialCustomListValue').delete_many(value_key, check_rev=False)
