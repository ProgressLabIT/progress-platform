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

@router.get('/issue-type',
    dependencies=[Depends(auth.verify_token)])
async def get_issue_type(
  key: str | None = None,
  code: str | None = None,
  critical: bool | None = None,
  active_only: bool = True
  ):
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

@router.post('/issue-type' , status_code=201,
    dependencies=[Depends(auth.verify_token)])
async def create_issue_type(data: IssueType):

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

@router.patch('/issue-type/{issue_type_key}',
    dependencies=[Depends(auth.verify_token)])
async def update_issue_type(issue_type_key: str, data: IssueTypeUpdate):

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

@router.delete('/issue-type/{issue_type_key}',
    dependencies=[Depends(auth.verify_token)])
async def delete_issue_type(issue_type_key: str):
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

@router.get('/issue',
    dependencies=[Depends(auth.verify_token)])
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

@router.get('/message',
    dependencies=[Depends(auth.verify_token)])
async def get_messages(recipient_id: str):
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

@router.get('/task', dependencies=[Depends(auth.verify_token)])
async def search_tasks(params: Annotated[TaskSearchParameters, Query()]):
  try:
    results = db.aql.execute(Queries.FIND_TASKS, bind_vars=params.model_dump())
    return [TaskSearchResult(**t) for t in results]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )



@router.get('/task/{task_key}', dependencies=[Depends(auth.verify_token)])
async def get_task_data(task_key: str):
  """
  Returns the task data with links to the issue, work order, product, etc.
  """
  try:
    task = db.aql.execute(Queries.GET_TASK_DATA, bind_vars=dict(task_key=task_key)).next()
    return task
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=traceback.format_exc()
    )


@router.get('/task-type', dependencies=[Depends(auth.verify_token)])
async def get_task_types(
    active_only: bool = True,
    name: str | None = None
):
    """Get task types, optionally filtered by active status and name"""
    try:
        query = {}
        if active_only:
            query["active"] = True
        if name:
            query["name"] = name

        cursor = db.collection('TaskType').find(query)
        return [TaskType(**t) for t in cursor]
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=traceback.format_exc()
        )

@router.post('/task-type', status_code=201, dependencies=[Depends(auth.verify_token)])
async def create_task_type(task_type: TaskType):
    """Create a new task type"""
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

@router.put('/task-type/{type_key}', dependencies=[Depends(auth.verify_token)])
async def update_task_type(type_key: str, task_type: TaskType):
    """Update an existing task type"""
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

@router.delete('/task-type/{type_key}', dependencies=[Depends(auth.verify_token)])
async def delete_task_type(type_key: str):
    """Delete a task type"""
    try:
        db.collection('TaskType').delete(type_key)
        return APIResponse(message="Task type deleted successfully")
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=traceback.format_exc()
        )
