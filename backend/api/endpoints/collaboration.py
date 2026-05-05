import traceback
from datetime import datetime
from typing import Annotated
from base64 import b64decode
import json

from fastapi import APIRouter, Body, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder

from models.collaboration import *
from utils.api import APIResponse
from utils import auth
from utils.db import db
from utils.collaboration import Queries

router = APIRouter()

issue_types = db.collection('IssueType')
issues = db.collection('Issue')
messages = db.collection('Message')

# ---------------------------------------------
# ISSUE TYPES
# ---------------------------------------------

@router.get(
  '/issue-type',
  response_model=list[IssueTypeFull],
  responses={
    500: {"description": "Database error while fetching issue types"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def get_issue_type(
  key: str | None = None,
  code: str | None = None,
  critical: bool | None = None,
  active_only: bool = True
  ):
  """List issue types, optionally filtered by key, code, or criticality.

  Executes `Queries.FETCH_ISSUE_TYPES` against ArangoDB with the provided
  filter parameters. Returns all active types by default; pass `active_only=false`
  to include archived types. Each result includes associated print templates.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:issue-type:read`
  """
  # use query parameters to filter specific type
  match = dict(
    key = key,
    code = code,
    critical = critical,
    active_only = active_only
  )

  cursor = db.aql.execute(Queries.FETCH_ISSUE_TYPES, bind_vars=match)
  return [IssueTypeFull(**it) for it in cursor]

# ----------------------------------------------------------------------

@router.post(
  '/issue-type',
  status_code=201,
  response_model=APIResponse,
  responses={
    409: {"description": "An issue type with the same code already exists"},
    500: {"description": "Database error during insertion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def create_issue_type(data: IssueType):
  """Create a new issue type.

  Inserts an `IssueType` document into the `IssueType` collection. Rejects
  the request with 409 if a document with the same `code` already exists.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:issue-type:write`
  """

  # Check if code already exists
  if issue_types.find({ 'code': data.code }).count():
    raise HTTPException(
      status_code=409,
      detail="An issue type with the same code already exists"
    )

  try:
    new_issue_type = issue_types.insert(data, return_new=True)['new']
    return APIResponse(
      status_code=201,
      message = f"Issue type { new_issue_type['_key'] } created correctly",
      detail = new_issue_type
    )

  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There has been a problem updating the database",
        error=traceback.format_exc()
      )
    )

# ----------------------------------------------------------------------

@router.patch(
  '/issue-type/{issue_type_key}',
  response_model=APIResponse,
  responses={
    500: {"description": "Database error during partial update"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def update_issue_type(issue_type_key: str, data: IssueTypeUpdate):
  """Partially update an existing issue type.

  Applies the supplied fields to the `IssueType` document identified by
  `issue_type_key`. Unset fields are left unchanged (`keep_none=False`).

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:issue-type:write`
  """

  if not hasattr(data, 'key'):
    data.key = issue_type_key

  try:
    updated_issue_type = issue_types.update(data.dict(by_alias=True), return_new=True, keep_none=False)['new']
    return APIResponse(
      message = "Issue type updated corretly",
      detail = updated_issue_type
    )

  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There has been a problem updating the database",
        error=traceback.format_exc()
      )
    )

# ----------------------------------------------------------------------

@router.delete(
  '/issue-type/{issue_type_key}',
  response_model=APIResponse,
  responses={
    500: {"description": "Database error during deletion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def delete_issue_type(issue_type_key: str):
  """Delete an issue type by key.

  Permanently removes the `IssueType` document with the given key from
  the collection. Existing `Issue` documents that reference this type
  are not automatically updated.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:issue-type:write`
  """
  try:
    issue_types.delete(issue_type_key)
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There has been a problem updating the database",
        error=traceback.format_exc()
      )
    )


# ---------------------------------------------
# ISSUES
# ---------------------------------------------

@router.get(
  '/issue',
  response_model=list[dict],
  responses={
    500: {"description": "AQL error while searching issues"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def search_issues(
  issue_key: list[str] | None = Query(default=None),
  issue_key_search: str | None = None,
  issue_type_key: list[str] | None = Query(default=None),
  product_key: list[str] | None = Query(default=None),
  product_code_search: str | None = None,
  work_order_key: list[str] | None = Query(default=None),
  work_order_code_search: str | None = None,
  serial_search: str | None = None,
  project_search: str | None = None,
  job_key: list[str] | None = Query(default=None),
  phase_key: list[str] | None = Query(default=None),
  phase_alias_search: str | None = None,
  operation_key: list[str] | None = Query(default=None),
  created_by: list[str] | None = Query(default=None),
  closed_by: list[str] | None = Query(default=None),
  time_created_from: datetime | None = None,
  time_created_to: datetime | None = None,
  time_closed_from: datetime | None = None,
  time_closed_to: datetime | None = None,
  issue_open: bool | None = None,
  issue_closed: bool | None = None,
  issue_critical: bool | None = None,
  issue_non_critical: bool | None = None,
  advanced_filters: str = Query(default=None),
  limit: int | None = None,
  offset: int | None = None,
  with_links: bool = False,
  sort_by: str | None = 'created',
  sorting_order: str | None = 'desc',
  ):
  """Search and filter issues with multi-dimensional query parameters.

  Executes `Queries.FIND_ISSUES` with all supplied filters. Filters are
  ANDed together; omitted parameters default to `null` and are ignored by
  the AQL query. `advanced_filters` accepts a base64-encoded JSON object
  (latin-1 encoding, matching the browser `btoa` API). Results are sorted
  by `sort_by` (default `created`) in `sorting_order` (default `desc`).

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:issue:read`
  """
  # use query parameters to filter specific type
  bind_vars = dict(
    issue_key = issue_key,
    issue_key_search = issue_key_search,
    issue_type_key = issue_type_key,
    product_key = product_key,
    product_code_search = product_code_search,
    work_order_key = work_order_key,
    work_order_code_search = work_order_code_search,
    project_search = project_search,
    serial_search = serial_search,
    job_key = job_key,
    phase_key = phase_key,
    phase_alias_search = phase_alias_search,
    operation_key = operation_key,
    created_by = created_by,
    closed_by = closed_by,
    time_created_from = time_created_from,
    time_created_to = time_created_to,
    time_closed_from = time_closed_from,
    time_closed_to = time_closed_to,
    issue_open = issue_open,
    issue_closed = issue_closed,
    issue_critical = issue_critical,
    issue_non_critical = issue_non_critical,
    # Browser API (btoa) encodes strings in latin-1 (ISO-8859-1)
    advanced_filters = json.loads(b64decode(advanced_filters).decode('latin-1')) if advanced_filters else None,
    limit = limit,
    offset = offset,
    with_links = with_links,
    #sort_by = sort_by,
    sorting_order = sorting_order
  )
  try:
    cursor = db.aql.execute(Queries.FIND_ISSUES.replace("<sort_by>", sort_by), bind_vars=bind_vars)
    return [i for i in cursor]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching issues from the db.",
        error=traceback.format_exc()
      )
    )


# ---------------------------------------------
# MESSAGES
# ---------------------------------------------

@router.get(
  '/message',
  response_model=list[Message],
  responses={
    500: {"description": "Database error while fetching messages"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def get_messages(recipient_id: str):
  """Retrieve messages for a given recipient, sorted by creation time.

  Queries the `message` edge collection filtering by `_to == recipient_id`.
  The recipient is typically an `Issue` or `User` document ID
  (e.g. `Issue/abc123`). Results are sorted ascending by `created` timestamp.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:message:read`
  """
  try:
    cursor = db.collection('message').find(dict(_to=recipient_id))
    messages = [Message(**m) for m in cursor]
    # Ensure sorting by posting time
    return sorted(messages, key=lambda m: m.created)
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching messages from the db.",
        error=traceback.format_exc()
      )
    )

# ---------------------------------------------
# TASKS
# ---------------------------------------------

@router.get(
  '/task',
  response_model=list[TaskSearchResult],
  responses={
    500: {"description": "AQL error while searching tasks"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def search_tasks(params: Annotated[TaskSearchParameters, Query()]):
  """Search tasks using multi-dimensional filter parameters.

  Executes `Queries.FIND_TASKS` with the bound `TaskSearchParameters`. Supports
  filtering by status flags, date ranges, assignees, and linked entities
  (issue, work order, product, serial). `advanced_filters` accepts a
  base64-encoded JSON object. Default limit is 200 rows.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:task:read`
  """
  try:
    results = db.aql.execute(Queries.FIND_TASKS, bind_vars=params.model_dump())
    return [TaskSearchResult(**t) for t in results]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )



@router.get(
  '/task/{task_key}',
  response_model=dict,
  responses={
    500: {"description": "AQL error while fetching task data"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def get_task_data(task_key: str):
  """Return full task data with linked entity references.

  Executes `Queries.GET_TASK_DATA` to fetch the `Task` document identified
  by `task_key` together with its graph links to issues, work orders, products,
  serials, and other tasks. Returns the raw AQL result dict.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:task:read`
  """
  try:
    task = db.aql.execute(Queries.GET_TASK_DATA, bind_vars=dict(task_key=task_key)).next()
    return task
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )


@router.get(
  '/task-type',
  response_model=list[TaskTypeFull],
  responses={
    500: {"description": "Database error while fetching task types"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def get_task_types(
    active_only: bool = True,
    name: str | None = None
):
  """List task types, optionally filtered by active status and name.

  Returns `TaskTypeFull` records (includes associated print templates).
  Pass `active_only=false` to include archived task types. `name` is a
  substring match against the type name field.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:task-type:read`
  """
  try:
    match = dict(
        active_only=active_only,
        name=name
    )

    cursor = db.aql.execute(Queries.FETCH_TASK_TYPES, bind_vars=match)
    return [TaskTypeFull(**t) for t in cursor]
  except Exception:
    raise HTTPException(
        status_code=500,
        detail=traceback.format_exc()
    )

@router.post(
  '/task-type',
  status_code=201,
  response_model=TaskType,
  responses={
    500: {"description": "Database error during task type insertion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def create_task_type(task_type: TaskType):
  """Create a new task type.

  Inserts a `TaskType` document into the `TaskType` collection. The
  `link_settings` field defaults to all entity types disabled; override
  explicitly to enable issue/work-order/product/serial/task linking for
  tasks of this type.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:task-type:write`
  """
  try:
      new_task_type = db.collection('TaskType').insert(
          task_type.model_dump(by_alias=True),
          return_new=True
      )['new']
      return TaskType(**new_task_type)
  except Exception:
      raise HTTPException(
          status_code=500,
          detail=traceback.format_exc()
      )

@router.put(
  '/task-type/{type_key}',
  response_model=APIResponse,
  responses={
    500: {"description": "Database error during task type replacement"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def update_task_type(type_key: str, task_type: TaskType):
  """Replace an existing task type document.

  Performs a full replacement of the `TaskType` document identified by
  `type_key`. Only fields present in the request body are written
  (`exclude_unset=True`), so omitted optional fields retain their current
  database values.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:task-type:write`
  """
  try:
      task_type.key = type_key
      updated_task_type = db.collection('TaskType').update(
          # Use exclude_unset to avoid updating fields that are not provided
          task_type.model_dump(by_alias=True, exclude_unset=True),
          return_new=True,
      )['new']
      return APIResponse(message="Task type updated successfully", detail=updated_task_type)
  except Exception:
      raise HTTPException(
          status_code=500,
          detail=traceback.format_exc()
      )

@router.delete(
  '/task-type/{type_key}',
  response_model=APIResponse,
  responses={
    500: {"description": "Database error during task type deletion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def delete_task_type(type_key: str):
  """Delete a task type by key.

  Permanently removes the `TaskType` document. Existing `Task` documents
  that reference this type via `task_type_key` are not automatically
  updated or removed.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `collaboration:task-type:write`
  """
  try:
      db.collection('TaskType').delete(type_key)
      return APIResponse(message="Task type deleted successfully")
  except Exception:
      raise HTTPException(
          status_code=500,
          detail=traceback.format_exc()
      )
