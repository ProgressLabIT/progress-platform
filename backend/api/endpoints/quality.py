import traceback
from datetime import datetime
from typing import Dict, List, Union

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder

from models.quality import *
from models.event import EventModel, EventType
from utils.api import APIResponse
from utils.db import db
from utils.quality import Queries

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
  return [_ for _ in cursor]

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
async def update_issue_type(issue_type_key: str, data: dict):

  if '_key' not in data:
    data['_key'] = issue_type_key

  try:
    updated_issue_type = issue_types.update(data, return_new=True, keep_none=False)['new']
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

@router.delete('/issue-type/{issue_key}')
async def delete_issue_type(issue_key: str):
  try:
    issue_types.delete(issue_key)
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
async def get_issues(
  issue_key: Union[List[str], None] = Query(default=None),
  issue_type: Union[List[str], None] = Query(default=None),
  product_key: Union[List[str], None] = Query(default=None),
  work_order_key: Union[List[str], None] = Query(default=None),
  job_key: Union[List[str], None] = Query(default=None),
  phase_key: Union[List[str], None] = Query(default=None),
  operation_key: Union[List[str], None] = Query(default=None),
  creator_id: Union[List[str], None] = Query(default=None),
  time_created_from: datetime = None,
  time_created_to: datetime = None,
  time_closed_from: datetime = None,
  time_closed_to: datetime = None,
  issue_open: bool = None,
  limit: int = None
  ):
  # use query parameters to filter specific type
  bind_vars = dict(
    issue_key = issue_key,
    issue_type = issue_type,
    product_key = product_key,
    work_order_key = work_order_key,
    job_key = job_key,
    phase_key = phase_key,
    operation_key = operation_key,
    creator_id = creator_id,
    time_created_from = time_created_from,
    time_created_to = time_created_to,
    time_closed_from = time_closed_from,
    time_closed_to = time_closed_to,
    issue_open = issue_open,
    limit = limit
  )
  cursor = db.aql.execute(Queries.FIND_ISSUES, bind_vars=bind_vars)
  return [i for i in cursor]

# ----------------------------------------------------------------------


@router.delete('/issue/{issue_key}')
async def delete_issue(issue_key: str):
  try:
    db.collection('Issue').delete(issue_key)
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error deleting the issue in the database.",
        error=traceback.format_exc()
      )
    )


# ---------------------------------------------
# MESSAGES
# ---------------------------------------------

@router.get('/message')
async def get_messages(issue_key: str):
  try:
    cursor = db.collection('message').find(dict(_to=f'Issue/{issue_key}'))
    return [Message(**m) for m in cursor]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching messages from the db.",
        error=traceback.format_exc()
      )
    )
