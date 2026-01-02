import os
import traceback
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File, Form
from fastapi.responses import Response

from models.inventory import *
from models.auth import TokenData
from utils.inventory import Queries
from utils.db import db
from utils import auth
from utils.api import APIResponse
from utils.counter import _generate_counter
from events.inventory.count_imported import (
  _parse_import_file,
  _validate_columns,
  _validate_import_rows,
  _generate_error_file,
  _detect_ignored_columns,
)


router = APIRouter()


# ========================================================
# COUNTING SESSIONS
# ========================================================

@router.post('/inventory/count-session')
def create_counting_session(
  count_session: InventoryCountSession,
  assignments: list[InventoryCountAssignmentNew],
  token: TokenData = Depends(auth.verify_token)
):
  try:
    tx = db.begin_transaction(write=['InventoryCountSession', 'InventoryCountAssignment', 'Config', 'Counter'])

    # Generate counting session code if not provided
    if count_session.code is None:
      counter_key = tx.collection('Config').get('system_counters').get('counting_sessions', 'default')
      try:
        count_session.code = _generate_counter(tx, counter_key)
      except Exception as e:
        raise Exception("Cannot generate counting session code. Please check if the counter is configured correctly.") from e

    # Set created_by on session
    count_session.created_by = token.consumer_key
    count_session_key = tx.collection('InventoryCountSession').insert(count_session.model_dump(by_alias=True))['_key']
    assignement_records = []
    for a in assignments:
      if a.targets is None or len(a.targets) == 0:
        raise HTTPException(status_code=400, detail="At least one item is required for each assignment")

      records = [InventoryCountAssignment(
        inventory_count_session_key=count_session_key,
        assigned_to=a.user_key,
        target_key=target.target_key,
        include_children=target.include_children,
        target_type=count_session.type,
        created_by=token.consumer_key,
        status=InventoryCountAssignmentStatus.PLANNED,
      ).model_dump(exclude=['key', 'id', 'rev']) for target in a.targets]

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


# ========================================================


@router.get('/inventory/count-session', dependencies=[Depends(auth.verify_token)])
def search_counting_sessions(params: Annotated[InventoryCountSessionSearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    cursor = db.aql.execute(Queries.SEARCH_INVENTORY_COUNT_SESSIONS, bind_vars=bind_vars)
    return [InventoryCountSession(**f) for f in cursor]
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


# ========================================================

@router.get('/inventory/count-session/{session_key}', dependencies=[Depends(auth.verify_token)])
def get_counting_session(session_key: str):
  try:
    session_data = db.aql.execute(
      Queries.GET_COUNT_SESSION_DETAILS,
      bind_vars=dict(inventory_count_session_key=session_key)
    ).next()
  except StopIteration:
    raise HTTPException(status_code=404, detail="Counting session not found")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

  return session_data


# ========================================================


@router.put('/inventory/count-session/{session_key}', dependencies=[Depends(auth.verify_token)])
def update_counting_session(
  session_key: str,
  session_update: InventoryCountSessionUpdate,
):
  try:
    # Fetch existing session
    session = InventoryCountSession(**db.collection('InventoryCountSession').get(session_key))
    if session is None:
      raise HTTPException(status_code=404, detail="Counting session not found")

    update_data = session_update.model_dump(by_alias=True, exclude_unset=True)


    if session.status != InventoryCountSessionStatus.PLANNED:
      can_update_only_if_planned = ['code', 'type', 'blind_quantities', 'blind_serials', 'scheduled_start']
      for field in can_update_only_if_planned:
        if update_data.get(field, None) is not None:
          raise HTTPException(status_code=422, detail=f"Cannot update {field} for a {session.status.value} session")

    # Update session
    update_data['_key'] = session_key
    db.collection('InventoryCountSession').update(update_data)
    return APIResponse(message = f"Counting session updated successfully")
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


# ========================================================


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


# ========================================================


@router.post('/inventory/count-assignment', dependencies=[Depends(auth.verify_token)])
def create_counting_assignments(
  assignments: list[InventoryCountAssignment],
  token: TokenData = Depends(auth.verify_token)
):
  try:
    if not assignments:
      raise HTTPException(status_code=400, detail="At least one assignment is required")

    # Validate all assignments belong to valid sessions
    session_keys = set(a.inventory_count_session_key for a in assignments)
    for session_key in session_keys:
      session = db.collection('InventoryCountSession').get(session_key)
      if not session:
        raise HTTPException(status_code=404, detail=f"Counting session {session_key} not found")

      session_status = InventoryCountSessionStatus(session['status'])
      if session_status in [InventoryCountSessionStatus.COMPLETED, InventoryCountSessionStatus.APPLIED, InventoryCountSessionStatus.CANCELED]:
        raise HTTPException(
          status_code=422,
          detail=f"Cannot add assignments to session {session['code']} - session is {session_status.value}"
        )

    # Set created_by for all assignments and ensure include_children defaults to False
    assignment_records = []
    for a in assignments:
      a.created_by = token.consumer_key
      if a.include_children is None:
        a.include_children = False
      assignment_records.append(a.model_dump(by_alias=True, exclude=['key', 'id', 'rev']))

    db.collection('InventoryCountAssignment').insert_many(assignment_records)
    return APIResponse(
      message = "Counting assignments created successfully",
      detail = dict(assignment_count=len(assignments))
    )
  except HTTPException:
    raise
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


# ========================================================


@router.delete('/inventory/count-assignment', dependencies=[Depends(auth.verify_token)])
def delete_counting_assignments(assignment_keys: list[str] = Body(..., embed=True)):
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

# ========================================================
# COUNTING RECORDS
# ========================================================

@router.get('/inventory/count-record', dependencies=[Depends(auth.verify_token)])
def get_counting_record(params: Annotated[InventoryCountRecordSearchParams, Query()]):
  try:
    bind_vars = dict(**params.model_dump())
    cursor = db.aql.execute(Queries.SEARCH_INVENTORY_COUNT_RECORDS, bind_vars=bind_vars)
    return list(cursor)
  except:
    raise HTTPException(status_code=500, detail=traceback.format_exc())


@router.get('/inventory/count-position-status')
async def get_count_position_status(
  session_key: str,
  parent_key: str
) -> dict[str, str]:
  """Get counting completion status for positions in a session, given a parent position key."""

  parent_id = f"Position/{parent_key}"
  session_id = f"InventoryCountSession/{session_key}"

  query = """
    LET children_ids = (
      FOR i IN 1..1 INBOUND @parent_id is_in_position
      FILTER IS_SAME_COLLECTION(Position, i)
      RETURN i._id
    )
    RETURN MERGE(
      FOR record IN inventory_count_position_complete
      FILTER record._from == @session_id && record._to IN children_ids
      RETURN { [PARSE_IDENTIFIER(record._to).key]: record.status }
    )
  """

  try:
    results = db.aql.execute(query, bind_vars=dict(
      session_id=session_id,
      parent_id=parent_id
    )).next()
  except Exception:
    raise HTTPException(status_code=500, detail=traceback.format_exc())

  # Return as dict for easy lookup
  return results


# ========================================================
# COUNT RECORD IMPORT
# ========================================================

@router.post('/inventory/count-record/import/validate')
async def validate_count_import(
  file: UploadFile = File(...),
  count_session_key: str = Form(...),
  import_mode: str = Form(...),
  token: TokenData = Depends(auth.verify_token)
):
  """
  Validate a count record import file.

  - Parses the uploaded CSV/XLSX file
  - Validates all product, position, and serial codes exist
  - If valid: stores file in media and returns file_key + summary
  - If errors: returns annotated Excel file with error details
  """
  try:
    # Validate import mode
    if import_mode not in ['update', 'replace']:
      raise HTTPException(status_code=400, detail="import_mode must be 'update' or 'replace'")

    # Validate session exists
    session = db.collection('InventoryCountSession').get(count_session_key)
    if not session:
      raise HTTPException(status_code=404, detail="Counting session not found")

    # Read file content
    file_content = await file.read()
    filename = file.filename or 'import.csv'

    # Parse file
    try:
      rows = _parse_import_file(file_content, filename)
    except ValueError as e:
      raise HTTPException(status_code=400, detail=str(e))

    if not rows:
      raise HTTPException(status_code=400, detail="No data rows found in file")

    # Validate required columns
    missing_columns = _validate_columns(rows)
    if missing_columns:
      raise HTTPException(
        status_code=400,
        detail=f"Missing required columns: {', '.join(missing_columns)}"
      )

    # Validate rows using a read-only transaction
    tx = db.begin_transaction(read=['Product', 'Position', 'Serial'])
    try:
      valid_rows, error_rows = _validate_import_rows(tx, rows, count_session_key)
    finally:
      tx.abort_transaction()  # Read-only, always abort

    # If errors, return annotated Excel file
    if error_rows:
      error_file_bytes = _generate_error_file(rows, error_rows)
      return Response(
        content=error_file_bytes,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
          'Content-Disposition': f'attachment; filename="import_errors.xlsx"',
          'X-Import-Status': 'error',
          'X-Error-Count': str(len(error_rows)),
          'X-Valid-Count': str(len(valid_rows)),
        }
      )

    # All valid - store file in media
    file_key = str(uuid.uuid4())
    media_path = os.environ.get('MEDIA_PATH', '/app/media')
    import_dir = os.path.join(media_path, 'count_import')
    os.makedirs(import_dir, exist_ok=True)

    file_path = os.path.join(import_dir, file_key)
    with open(file_path, 'wb') as f:
      f.write(file_content)

    # Count existing records that would be affected
    existing_count = 0
    if import_mode == 'replace':
      cursor = db.aql.execute('''
        FOR r IN inventory_count_record
        FILTER r.inventory_count_session_key == @session_key
          AND r.status IN ['completed', 'submitted', 'confirmed']
        RETURN 1
      ''', bind_vars={'session_key': count_session_key})
      existing_count = len(list(cursor))
    else:
      # Update mode - count matching product/position pairs
      product_position_pairs = set()
      for row in valid_rows:
        product_position_pairs.add((row['product_key'], row['position_key']))

      for product_key, position_key in product_position_pairs:
        cursor = db.aql.execute('''
          FOR r IN inventory_count_record
          FILTER r._from == @product_id
            AND r._to == @position_id
            AND r.inventory_count_session_key == @session_key
            AND r.status IN ['completed', 'submitted', 'confirmed']
          RETURN 1
        ''', bind_vars={
          'product_id': f'Product/{product_key}',
          'position_id': f'Position/{position_key}',
          'session_key': count_session_key,
        })
        existing_count += len(list(cursor))

    # Count unique product/position pairs for import
    unique_pairs = set()
    for row in valid_rows:
      unique_pairs.add((row['product_key'], row['position_key']))

    # Detect columns that will be ignored
    ignored_columns = _detect_ignored_columns(rows)

    return {
      'status': 'valid',
      'file_key': file_key,
      'filename': filename,
      'rows_total': len(rows),
      'rows_valid': len(valid_rows),
      'records_to_add': len(unique_pairs),
      'records_to_discard': existing_count,
      'import_mode': import_mode,
      'ignored_columns': ignored_columns,
    }

  except HTTPException:
    raise
  except Exception:
    raise HTTPException(status_code=500, detail=traceback.format_exc())
