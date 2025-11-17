import traceback
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from models.inventory import *
from utils.inventory import Queries
from utils.db import db
from utils import auth
from utils.api import APIResponse
from utils.counter import _generate_counter


router = APIRouter()


# ========================================================
# COUNTING SESSIONS
# ========================================================

@router.post('/inventory/count-session', dependencies=[Depends(auth.verify_token)])
def create_counting_session(count_session: InventoryCountSession, assignments: list[InventoryCountAssignmentNew]):
  try:
    if len(assignments) == 0:
      raise HTTPException(status_code=400, detail="At least one assignment is required")
    tx = db.begin_transaction(write=['InventoryCountSession', 'InventoryCountAssignment', 'Config', 'Counter'])

    # Generate counting session code if not provided
    if count_session.code is None:
      counter_key = tx.collection('Config').get('system_counters').get('counting_sessions', 'default')
      try:
        count_session.code = _generate_counter(tx, counter_key)
      except Exception as e:
        raise Exception("Cannot generate counting session code. Please check if the counter is configured correctly.") from e

    count_session_key = tx.collection('InventoryCountSession').insert(count_session.model_dump(by_alias=True))['_key']
    assignement_records = []
    for a in assignments:
      if a.target_keys is None or len(a.target_keys) == 0:
        raise HTTPException(status_code=400, detail="At least one item is required for each assignment")

      records = [InventoryCountAssignment(
        inventory_count_session_key=count_session_key,
        assigned_to=a.user_key,
        target_key=target_key,
        target_type=count_session.type,
      ).model_dump(by_alias=True) for target_key in a.target_keys]

      assignement_records.extend(records)

    tx.collection('InventoryCountAssignment').insert_many(assignement_records)
    tx.commit_transaction()

    return APIResponse(
      message = f"Counting session {count_session.code} created successfully",
      detail = dict(count_session_key=count_session_key, code=count_session.code)
    )
  except:
    tx.abort_transaction()
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get('/inventory/count-session', dependencies=[Depends(auth.verify_token)])
def search_counting_sessions(params: Annotated[InventoryCountSessionSearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    cursor = db.aql.execute(Queries.SEARCH_INVENTORY_COUNT_SESSIONS, bind_vars=bind_vars)
    return [InventoryCountSession(**f) for f in cursor]
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.delete('/inventory/count-session', dependencies=[Depends(auth.verify_token)])
def delete_counting_session(counting_session_key: str):
  try:
    session = db.collection('InventoryCountSession').get(counting_session_key)
    if not session:
      raise HTTPException(status_code=404, detail="Counting session not found")

    if session['status'] != InventoryCountSessionStatus.PLANNED:
      raise HTTPException(status_code=422, detail="Counting session cannot be deleted because it has been started or completed.")

    tx = db.begin_transaction(write=['InventoryCountSession', 'InventoryCountAssignment'])
    tx.collection('InventoryCountSession').delete(counting_session_key)
    tx.collection('InventoryCountAssignment').delete_match(dict(inventory_count_session_key=counting_session_key))
    tx.commit_transaction()
    return APIResponse(message = f"Counting session {session['code']} deleted successfully")
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


# ========================================================
# COUNTING ASSIGNMENTS
# ========================================================

@router.get('/inventory/count-assignment', dependencies=[Depends(auth.verify_token)])
def get_counting_assignment(params: Annotated[InventoryCountAssignmentSearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    cursor = db.aql.execute(Queries.SEARCH_INVENTORY_COUNT_ASSIGNMENTS, bind_vars=bind_vars)
    return [InventoryCountAssignment(**f) for f in cursor]
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.post('/inventory/count-assignment', dependencies=[Depends(auth.verify_token)])
def create_counting_assignments(assignments: list[InventoryCountAssignment]):
  try:
    db.collection('InventoryCountAssignment').insert_many([a.model_dump() for a in assignments])
    return APIResponse(
      message = "Counting assignments created successfully",
      detail = dict(assignment_count=len(assignments))
    )
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.delete('/inventory/count-assignment', dependencies=[Depends(auth.verify_token)])
def delete_counting_assignments(assignment_keys: list[str]):
  try:
    tx = db.begin_transaction(write=['InventoryCountAssignment'])
    removed = list(tx.aql.execute(Queries.CANCEL_INVENTORY_COUNT_ASSIGNMENTS, bind_vars=dict(assignment_keys=assignment_keys)))

    if len(removed) < len(assignment_keys):
      tx.abort_transaction()
      raise HTTPException(status_code=400, detail="Operation aborted: some assignments cannot be canceled because they have been started or completed.")

    tx.commit_transaction()
    return APIResponse(
      message = "Counting assignments canceled successfully",
      detail = dict(assignment_count=len(assignment_keys))
    )
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())

