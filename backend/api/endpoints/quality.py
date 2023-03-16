import traceback
from datetime import datetime
from typing import Dict, List, Union

from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder

from models.quality import *
from utils.db import db

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
  ):
  # use query parameters to filter specific type
  match = dict()
  if key:
    match['_key'] = key
  if code:
    match['code'] = code
  if critical:
    match['critical'] = critical

  return [_ for _ in issue_types.find(match)]


@router.post('/issue-type' , response_status=201)
async def create_issue_type(data: IssueType):

  # Check if code already exists
  try:
    if issue_types.find({ 'code': data.code }).count():
      raise HTTPException(
        status_code=409,
        detail="An issue type with the same code already exists"
      )

    new_issue_type = issue_types.insert(data, return_new=True)['new']
    return APIResponse(
      status_code=201,
      message = f"Issue type created { new_issue_type['_key'] } updated correctly",
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


@router.put('/issue-type/{issue_type_ref}')
async def update_issue_type(
  issue_type_ref: str,
  data: IssueType,
  by_code = False
  ):

  search_field = 'code' if by_code else '_key'
  match = { search_field: issue_type_ref }

  try:
    updated_issue_type = issue_types.replace_match(match, data, return_new=True, keep_none=False)['new']
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
async def get_issue(
  id: str = None,
  issue_type: str = None,
  product_code: str = None,
  product_key: str = None,
  work_order_code: str = None,
  work_order_key: str = None,
  job_key: str = None,
  phase_key: str = None,
  operation_key: str = None,
  creator_id: str = None,
  time_created_from: datetime = None,
  time_created_to: datetime = None,
  time_closed_from: datetime = None,
  time_closed_to: datetime = None,
  open: bool = None,
  limit: int = None
  ):
  # use query parameters to filter specific type
  pass


@router.post('/issue')
async def create_issue(data: IssueWithLinks):
  pass


@router.patch('/issue/{issue_key}')
async def update_issue(
  title: str = Body(None),
  description: str = Body(None),
  issue_type: str = Body(None),
  critical: bool = Body(None),
  open: bool = Body(None),
  field_update: IssueField
  ):



@router.delete('/issue/{issue_key}')
async def cancel_issue(issue_key: str):
  pass


# ---------------------------------------------
# MESSAGES
# ---------------------------------------------

@router.post('/message')
async def post_message(id: str):
# use query parameters to filter specific type
  pass


@router.patch('/message/{message_key}')
async def update_message(content: str = Body()):
  pass


@router.delete('/message/{message_key}')
async def delete_message(message_key: str):
  # Dont't really delete it, simply flag it as deleted.
  pass
