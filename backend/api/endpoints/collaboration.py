import traceback
from datetime import datetime
from typing import Dict, List, Union
from base64 import b64decode
import json

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from models.collaboration import *
from models.event import EventModel, EventType
from utils.api import APIResponse
from utils.db import db
from utils.collaboration import Queries

router = APIRouter()

issue_types = db.collection('IssueType')
issues = db.collection('Issue')
messages = db.collection('Message')

# ---------------------------------------------
# ISSUE TYPES
# ---------------------------------------------

@router.get('/issue-type')
async def get_issue_type(
  key: str = None,
  code: str = None,
  critical: bool = None,
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

@router.post('/issue-type' , status_code=201)
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

@router.patch('/issue-type/{issue_type_key}')
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

@router.delete('/issue-type/{issue_type_key}')
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

@router.get('/issue')
async def search_issues(
  issue_key: Union[List[str], None] = Query(default=None),
  issue_key_search: str = None,
  issue_type_key: Union[List[str], None] = Query(default=None),
  product_key: Union[List[str], None] = Query(default=None),
  product_code_search: str = None,
  work_order_key: Union[List[str], None] = Query(default=None),
  work_order_code_search: str = None,
  project_search: str = None,
  job_key: Union[List[str], None] = Query(default=None),
  phase_key: Union[List[str], None] = Query(default=None),
  phase_alias_search: str = None,
  operation_key: Union[List[str], None] = Query(default=None),
  created_by: Union[List[str], None] = Query(default=None),
  closed_by: Union[List[str], None] = Query(default=None),
  time_created_from: datetime = None,
  time_created_to: datetime = None,
  time_closed_from: datetime = None,
  time_closed_to: datetime = None,
  issue_open: bool = None,
  issue_closed: bool = None,
  issue_critical: bool = None,
  issue_non_critical: bool = None,
  advanced_filters: str = Query(default=None),
  limit: int = None,
  with_links: bool = False
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
    with_links = with_links
  )
  cursor = db.aql.execute(Queries.FIND_ISSUES, bind_vars=bind_vars)
  return [i for i in cursor]


# ---------------------------------------------
# MESSAGES
# ---------------------------------------------

@router.get('/message')
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
