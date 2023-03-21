import traceback
from datetime import datetime
from typing import Dict, List, Union

from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder

from models.quality import *
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
async def get_issue(
  issue_key: str = None,
  issue_type: str = None,
  product_key: str = None,
  work_order_key: str = None,
  job_key: str = None,
  phase_key: str = None,
  operation_key: str = None,
  creator_id: str = None,
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
  return [Issue(**i) for i in cursor]

# ----------------------------------------------------------------------

def build_link(_from: str, link_dict: IssueLink):
  link_map = dict(
    product="Product/",
    operation="Operation/",
    phase="Phase/",
    work_order="WorkOrder/",
    project="Project/",
    user="User/",
    job="Job/"
  )
  target = link_map[link_dict.type.value] + link_dict.key
  return dict(_from=_from, _to=target)

@router.post('/issue')
async def create_issue(data: IssueWithLinks):
  try:
    tx = db.begin_transaction(write=['Issue', 'issue_rel'])
    new_issue_id = tx.collection('Issue').insert(Issue(**data.dict()))['_id']

    rels = [build_link(_from=new_issue_id, link_dict=rel) for rel in data.linked_to]

    tx.collection('issue_rel').insert_many(rels, silent=True)
    tx.commit_transaction()
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error creating the issue in the database.",
        error=traceback.format_exc()
      )
    )

# ----------------------------------------------------------------------

@router.patch('/issue/{issue_key}')
async def update_issue(
  title: str = Body(None),
  description: str = Body(None),
  issue_type: str = Body(None),
  critical: bool = Body(None),
  open: bool = Body(None),
  field_updates: List[IssueField] = None
  ):

  new_data = dict(_key = issue_key)

  if title:
    new_data['title'] = title

  if description:
    new_data['description'] = description

  if issue_type:
    new_data['issue_type'] = issue_type

  if critical:
    new_data['critical'] = critical

  if open:
    new_data['open'] = open

  try:
    updated_issue = db.collection('Issue').update(new_data, return_new=True)['new']
    return APIResponse(
      message=f"Issue { updated_issue['_key'] } updated successfully",
      detail=updated_issue
    )

  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error updating the issue in the database.",
        error=traceback.format_exc()
      )
    )

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



@router.post('/message')
async def post_message(data: Message):
# use query parameters to filter specific type
  try:
    new_message = db.collection('message').insert(data, return_new=True)['new']
    return APIResponse(
      message="The message was posted correctly",
      detail=new_message
    )
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error posting the message.",
        error=traceback.format_exc()
      )
    )

# ----------------------------------------------------------------------

@router.patch('/message/{message_key}')
async def update_message(content: str = Body()):
  try:
    update = dict(_key=message_key, content=content)
    updated_content = db.collection('message').update(update, return_new=True)['new']
    return APIResponse(
      message="The message was updated correctly",
      detail=updated_content
    )
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error updating the message.",
        error=traceback.format_exc()
      )
    )

# ----------------------------------------------------------------------

@router.delete('/message/{message_key}')
async def delete_message(message_key: str):
  # Dont't really delete it, simply flag it as deleted.
  try:
    update = dict(_key=message_key, deleted=True)
    db.collection('message').update(update)
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error updating the message.",
        error=traceback.format_exc()
      )
    )
