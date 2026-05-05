import re
import traceback

from fastapi import APIRouter, HTTPException, Query, Depends
from utils import auth

from utils.api import APIResponse
from models.form import CustomField, CustomListValue, FieldType
from utils.db import db, model_to_db_dict

router = APIRouter()


def slugify(name: str) -> str:
    """Convert a human label to a stable snake_case identifier (mirrors JS slugify in templateResolver.js)."""
    s = name.lower()
    s = re.sub(r'\([^)]*\)', '', s)   # remove parenthesised content
    s = re.sub(r'[^a-z0-9]+', '_', s)  # non-alphanumeric runs → '_'
    s = re.sub(r'_+', '_', s)          # collapse consecutive underscores
    return s.strip('_')


@router.post('/field',
    response_model=APIResponse,
    responses={
      409: {"description": "A custom field with the same slug already exists"},
      500: {"description": "Database insert or slug-check error"},
    },
    dependencies=[Depends(auth.verify_token)])
def create_field(field_data: CustomField):
  """Create a new custom field definition.

  Inserts a `CustomField` document after verifying that no existing field
  produces the same slug (derived by converting the `name` to snake_case).
  The slug is used as the field identifier in form templates and data exports.

  Returns HTTP 409 if the slug already exists.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:form:create`
  """
  slug = slugify(field_data.name)
  try:
    existing = list(db.aql.execute(
      'FOR f IN CustomField RETURN { _key: f._key, name: f.name }'
    ))
    if any(slugify(f['name']) == slug for f in existing):
      raise HTTPException(status_code=409, detail=f"A custom field with slug '{slug}' already exists")
  except HTTPException:
    raise
  except Exception:
    raise HTTPException(status_code=500, detail=traceback.format_exc())
  try:
    field_key = db.collection('CustomField').insert(field_data)['_key']
    return APIResponse(
      message = "Field created successfully",
      detail = dict(field_key=field_key)
    )
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get('/field',
    response_model=list,
    responses={500: {"description": "Database query error"}},
    dependencies=[Depends(auth.verify_token)])
def fetch_field(name: str | None = None, key: str | None = None):
  """Fetch custom field definitions, optionally filtered by name or key.

  Returns all `CustomField` documents sorted alphabetically by name.
  Pass `name` to filter by exact field name, or `key` to fetch a single
  field by its ArangoDB `_key`. Both filters can be combined.

  **Emits:** *(direct query — no event class)*

  **Required scope:** `quality:form:read`
  """
  match = dict()
  if name:
    match['name'] = name
  if key:
    match['_key'] = key

  cursor = db.collection('CustomField').find(match)
  result = [CustomField(**f) for f in cursor]
  return sorted(result, key=lambda x: x.name.lower())



@router.put('/field/{field_key}',
    response_model=APIResponse,
    responses={
      409: {"description": "Another field with the same slug already exists"},
      500: {"description": "Database update or slug-check error"},
    },
    dependencies=[Depends(auth.verify_token)])
def replace_field_metadata(field_key: str, field_data: CustomField):
  """Replace a custom field definition.

  Performs a full replace of the `CustomField` document identified by
  `field_key`. Validates that the resulting slug does not collide with any
  other existing field (self-collision is allowed). Returns HTTP 409 on
  conflict.

  The payload must include `_key` in `field_data`.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:form:update`
  """
  slug = slugify(field_data.name)
  try:
    existing = list(db.aql.execute(
      'FOR f IN CustomField RETURN { _key: f._key, name: f.name }'
    ))
    if any(slugify(f['name']) == slug and f['_key'] != field_key for f in existing):
      raise HTTPException(status_code=409, detail=f"A custom field with slug '{slug}' already exists")
  except HTTPException:
    raise
  except Exception:
    raise HTTPException(status_code=500, detail=traceback.format_exc())
  try:
    db.collection('CustomField').update(field_data.dict(by_alias=True), check_rev=False)
    return APIResponse(message = "Field updated successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.delete('/field/{field_key}',
    response_model=APIResponse,
    responses={500: {"description": "Database delete error"}},
    dependencies=[Depends(auth.verify_token)])
def delete_field(field_key: str):
  """Delete a custom field and all its associated list values.

  Removes the `CustomField` document and, if the field type is `choice`,
  deletes all linked `CustomListValue` documents in the same transaction.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:form:update`
  """
  try:
    tx = db.begin_transaction(write=['CustomField', 'CustomListValue'])
    deleted = tx.collection('CustomField').delete(field_key, return_old=True)['old']

    # Delete list values
    if CustomField(**deleted).type == FieldType.CHOICE:
      tx.collection('CustomListValue').delete_match(dict(field_key=field_key))

    tx.commit_transaction()

    return APIResponse(message = "Field deleted successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.get('/list',
    response_model=list,
    responses={500: {"description": "Database query error"}},
    dependencies=[Depends(auth.verify_token)])
def fetch_custom_list_values(
  field_key: str,
  limit: int = 100,
  search: str | None = None,
  sort_by: str = 'value'
  ):
  """Fetch paginated list values for a choice-type custom field.

  Returns up to `limit` `CustomListValue` records for the given `field_key`,
  sorted by `sort_by`. Pass `search` to filter by a substring match across
  both `value` and `ext_key` (case-insensitive).

  **Emits:** *(direct query — no event class)*

  **Required scope:** `quality:form:read`
  """
  query = """
    FOR v IN CustomListValue
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


@router.post('/list/{field_key}',
    response_model=None,
    responses={500: {"description": "Database insert/replace error"}},
    dependencies=[Depends(auth.verify_token)])
def create_or_update_custom_list_values(
  field_key: str,
  new_values: list[CustomListValue],
  reset: bool = False
  ):
  """Bulk upsert list values for a choice-type custom field.

  Inserts or replaces `CustomListValue` records for `field_key`. When
  `reset=true`, all existing values for the field are deleted before
  inserting `new_values`, performing a full replacement. When `reset=false`,
  supplied values are upserted (insert-or-replace by `_key`).

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:form:update`
  """
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

@router.delete('/list/{field_key}',
    response_model=None,
    responses={500: {"description": "Database delete error"}},
    dependencies=[Depends(auth.verify_token)])
def delete_custom_list_value(
  field_key: str,
  value_key: list[str] = Query(...)
  ):
  """Delete specific list values from a choice-type custom field.

  Removes the `CustomListValue` documents whose `_key` is in `value_key`
  (repeated query parameter). Only values belonging to `field_key` are
  targeted by the URL path; the deletion itself operates on `_key` only.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `quality:form:update`
  """
  db.collection('CustomListValue').delete_many(value_key, check_rev=False)
