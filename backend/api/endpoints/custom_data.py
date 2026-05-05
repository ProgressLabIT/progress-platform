import traceback

from fastapi import APIRouter, HTTPException, Depends
from utils import auth
from utils.api import APIResponse
from models.custom_data import CustomData, KEY_PATTERN, KEY_MAX_LENGTH
from utils.db import db

router = APIRouter()

COLLECTION = 'CustomData'


def _validate_key(key: str):
    """Validate _key format. Raises 422 if invalid."""
    if not KEY_PATTERN.match(key) or len(key) > KEY_MAX_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f'Key must match {KEY_PATTERN.pattern} and be at most {KEY_MAX_LENGTH} chars',
        )


@router.get(
  '/custom-data',
  response_model=list[CustomData],
  responses={},
  dependencies=[Depends(auth.verify_token)],
)
def list_custom_data(search: str | None = None):
    """List all custom-data entries, optionally filtered by a search string.

    Executes an AQL query against the `CustomData` collection. When `search`
    is provided, filters by case-insensitive substring match against both the
    document `_key` and the `description` field. Results are sorted by `_key`.

    **Emits:** *(direct transaction — no event class)*

    **Required scope:** `admin:custom-data:read`
    """
    query = """
        FOR d IN CustomData
        FILTER @search == null
            OR CONTAINS(LOWER(d._key), LOWER(@search))
            OR CONTAINS(LOWER(d.description || ''), LOWER(@search))
        SORT d._key
        RETURN d
    """
    cursor = db.aql.execute(query, bind_vars=dict(search=search))
    return [CustomData(**d) for d in cursor]


@router.get(
  '/custom-data/{key}',
  response_model=CustomData,
  responses={
    404: {"description": "No CustomData document exists for the given key"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def get_custom_data(key: str):
    """Retrieve a single custom-data entry by key.

    Looks up the `CustomData` document with `_key == key`. Returns 404 if
    no document exists for that key.

    **Emits:** *(direct transaction — no event class)*

    **Required scope:** `admin:custom-data:read`
    """
    doc = db.collection(COLLECTION).get(key)
    if not doc:
        raise HTTPException(status_code=404, detail=f'CustomData {key!r} not found')
    return CustomData(**doc)


@router.put(
  '/custom-data/{key}',
  response_model=APIResponse,
  responses={
    422: {"description": "Key fails format validation (must match `^[a-z][a-z0-9_]*$`, max 64 chars)"},
    500: {"description": "Database error during upsert"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def upsert_custom_data(key: str, body: CustomData):
    """Create or replace a custom-data entry.

    Validates `key` format (lowercase alphanumeric + underscore, max 64 chars),
    then inserts or replaces the `CustomData` document. Existing documents are
    fully replaced (`check_rev=False`). Returns a message indicating whether
    the entry was created or updated.

    **Emits:** *(direct transaction — no event class)*

    **Required scope:** `admin:custom-data:write`
    """
    _validate_key(key)
    doc = body.model_dump(by_alias=True, exclude_none=True)
    doc['_key'] = key

    collection = db.collection(COLLECTION)
    existing = collection.get(key)

    try:
        if existing:
            collection.replace(doc, check_rev=False)
            message = f'CustomData {key!r} updated'
        else:
            collection.insert(doc)
            message = f'CustomData {key!r} created'
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

    return APIResponse(message=message, detail=dict(_key=key))


@router.delete(
  '/custom-data/{key}',
  response_model=APIResponse,
  responses={
    404: {"description": "No CustomData document exists for the given key"},
    500: {"description": "Database error during deletion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def delete_custom_data(key: str):
    """Delete a custom-data entry by key.

    Returns 404 if the document does not exist. On success, permanently
    removes the `CustomData` document from the collection.

    **Emits:** *(direct transaction — no event class)*

    **Required scope:** `admin:custom-data:write`
    """
    collection = db.collection(COLLECTION)
    if not collection.get(key):
        raise HTTPException(status_code=404, detail=f'CustomData {key!r} not found')

    try:
        collection.delete(key)
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

    return APIResponse(message=f'CustomData {key!r} deleted')
