import traceback

from fastapi import APIRouter, HTTPException, Query, Depends

from utils.api import APIResponse
from models.counter import Counter
from utils.db import db
from utils import auth

router = APIRouter()


@router.post(
  '/counter',
  response_model=APIResponse,
  responses={
    500: {"description": "Database error during counter insertion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def create_counter(counter_data: Counter):
  """Create a new counter sequence definition.

  Inserts a `Counter` document into the `Counter` collection. The counter
  template and frequency determine how the sequence string is formatted and
  when the tick resets. Returns the new counter's `_key`.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `traceability:counter:write`
  """
  try:
    counter_key = db.collection('Counter').insert(counter_data)['_key']
    return APIResponse(
      message = "Counter created successfully",
      detail = dict(counter_key=counter_key)
    )
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get(
  '/counter',
  response_model=list[Counter],
  responses={
    500: {"description": "Database error while fetching counters"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def fetch_counter(name: str | None = None, key: str | None = None):
  """List counters, optionally filtered by name or key.

  Queries the `Counter` collection with the provided filters. Returns all
  counters when no filters are supplied, sorted ascending by name (case-insensitive).

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `traceability:counter:read`
  """
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



@router.put(
  '/counter/{counter_key}',
  response_model=APIResponse,
  responses={
    500: {"description": "Database error during counter update"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def replace_field_metadata(counter_key: str, counter_data: Counter):
  """Replace counter metadata for a given counter key.

  Performs a full document update of the `Counter` record identified by
  `counter_key`. The request body must include `_key` (via the `counter_data`
  model). `check_rev=False` means optimistic concurrency is not enforced.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `traceability:counter:write`
  """
  try:
    db.collection('Counter').update(counter_data.dict(by_alias=True), check_rev=False)
    return APIResponse(message = "Counter updated successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())



@router.delete(
  '/counter/{counter_key}',
  response_model=APIResponse,
  responses={
    409: {"description": "Counter is assigned as a system counter slot or referenced by one or more Products"},
    500: {"description": "Database error during deletion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def delete_field(counter_key: str):
  """Delete a counter sequence definition.

  Refuses deletion (409) if the counter is assigned to a system counter slot
  (checked via the `Config/system_counters` document) or if any `Product`
  document references it via `counter_key`. Returns 200 on successful deletion.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `traceability:counter:write`
  """
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
