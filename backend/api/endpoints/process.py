import os
import traceback
from enum import Enum
from typing import List, Optional
from fnmatch import fnmatch

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from models.process import *
from utils import dt
from utils.api import APIResponse
from utils.db import db
from utils.file import UserFile
from utils.process import *


router = APIRouter()

operation_db = db.collection('Operation')




@router.get('/operation')
async def get_operation_list():
  
  def enrich_op_data(op_data):
    op_data['used_for'] = get_products_using_operation(op_data['_key'])
    return op_data

  db_list = [enrich_op_data(o) for o in operation_db.all()]
  # Sort by operation name
  return sorted(db_list, key=lambda o: o['name'].lower())



@router.post('/operation')
async def create_operation(new_op_data: Operation):

  try:
    new_op_record = operation_db.insert(new_op_data, return_new=True)['new']
    return APIResponse(detail=new_op_record, message="Operation created successfully")

  except:
    status_code = 500
    message = "Could not save new operation, please contact the administrator."
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message=message,
      error=error_str
    )
    raise HTTPException(status_code=status_code, detail=response)


@router.patch('/operation/{op_key}')
async def update_operation(op_key: str, op_update: dict):
  
  try:
    updated_op_record = operation_db.update(dict(_key=op_key, **op_update), return_new=True)['new']
    return APIResponse(message="Operation updated successfully", detail=updated_op_record)

  except:
    status_code = 500
    response=dict(
      status_code=status_code,
      message="Could not update Operation in the db. Please contact the administrator.",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)



@router.delete('/operation/{op_key}')
async def delete_operation(op_key: str):

  try: 
    is_used_for_products = [p.code for p in get_products_using_operation(op_key)]

  except:
    status_code = 500
    response = dict(
      status_code=status_code,
      message="Couldn't delete Operation from DB due to a server error. Please contact the administrator.",
      error=traceback.format_exc()
    )
    raise HTTPException(status_code=status_code, detail=response)

  # Delete operation only if is not used
  if len(is_used_for_products):
    status_code = 403
    response = dict(
      status_code=status_code,
      message=f"Operation cannot be deleted because it is in use in the process of the following products.",
      product_codes=is_used_for_products
    )
    raise HTTPException(status_code=status_code, detail=response)

  else:
    removed_op = db.collection('Operation').delete(dict(_key=op_key), return_old=True)['old']
    return APIResponse(message="Operation successfully deleted", detail=removed_op)

  

@router.get("/step/{step_key}/media")
async def get_step_media(step_key: str):
  return search_step_media(step_key)



@router.get("/product/{product_key}/process")
async def get_production_process(product_key):

  try:
    process_data = db.aql.execute(
      Queries.GET_PRODUCTION_PROCESS, 
      bind_vars=dict(product_key=product_key)
    )

  except Exception as e:
    status_code = 500
    message = "Couldn't fetch data from the db"
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message=message,
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )
  
  try:
    results = [PhaseData(**phase) for phase in process_data]
    
  except Exception as e:
    status_code = 500
    message = "Error validating data from DB"
    error_str = traceback.format_exc()
    response = dict(
      status=status_code,
      message=message,
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  return results


@router.put(
  "/product/{product_key}/process", 
  response_model = List[PhaseUpdate],
  response_model_exclude = {'step_sequence'}
)
async def update_process(process: List[PhaseUpdate], product_key):
 
  
  tx_db = db.begin_transaction(write=['Product', 'Phase', 'Step', 'requires'])
  timestamp = dt.timestamp()
  new_phase_sequence = []

  try:
  # LOOP OVER PHASES TO UPDATE DB
    for seq, phase in enumerate(process):

      # Insert/replace steps
      for index, s in enumerate(phase.steps):
        exclude_set = { 'key' } if s.key == None else None
        prepped_step_data = jsonable_encoder(s, by_alias=True, exclude=exclude_set)

        step_update = tx_db.insert_document('Step', 
          prepped_step_data, overwrite=True, return_new=True )

        phase.steps[index] = step_update['new']
        phase.step_sequence.append(step_update['_key'])

      # Flag removed steps for deletion by TTL 
      old_step_sequence = tx_db.document(f'Phase/{phase.key}')['step_sequence'] if phase.key else []
      removed_steps = [s for s in old_step_sequence if s not in phase.step_sequence]

      for r in removed_steps:
        tx_db.collection('Step').update(dict(_key=r, trashed=timestamp))

      # Insert/replace phase
      exclude_set = { 'steps', 'operation_key' }
      # do not 'export' _id field with value null if none is set, so that the DB 
      # will set it automatically
      new_phase = True if phase.key == None else False

      if new_phase: exclude_set.add('key')
      prepped_phase_data = jsonable_encoder(phase, by_alias=True, exclude=exclude_set)
      
      phase_update = tx_db.insert_document('Phase', 
        prepped_phase_data, return_new=True, overwrite=True )
      
      if new_phase:
        # Insert new ProductPhase relationship
        new_phase_id=f"Phase/{phase_update['_key']}"
        tx_db.insert_document('requires', dict(
          _from=f'Product/{product_key}',
          _to=new_phase_id,
          type='ProductPhase'
        ))

        # Insert new PhaseOperation relationship
        tx_db.insert_document('requires', dict(
          _from=new_phase_id,
          _to=f'Operation/{phase.operation_key}',
          type='PhaseOperation'
        ))

        process[seq].key = phase_update['_key']

      new_phase_sequence.append(phase_update['_key'])

    # Update new sequence, returning old one for deletion check
    phase_sequence_update = tx_db.collection('Product').update(dict(
      _key=product_key, 
      process_phases=new_phase_sequence 
    ), return_old=True)

    # Flag removed phases (and relationships) for deletion by TTL index
    old_phase_sequence = phase_sequence_update['old']['process_phases']
    removed_phases = [p for p in old_phase_sequence if p not in new_phase_sequence]

    for p in removed_phases:
      # Flag phase document
      tx_db.collection('Phase').update(dict(_key=p, trashed=timestamp))
      
      # Flag phase relationships
      tx_db.aql.execute(
        Queries.TRASH_FLAG_PHASE_RELATIONSHIP, 
        bind_vars=dict(phase_key=p, timestamp=timestamp)
      )

    # Commit transaction
    tx_db.commit_transaction()

    return process

  except Exception as e:
    tx_id = tx_db.transaction_id
    error_str = traceback.format_exc()
    response = dict(
      exception=e,
      transaction=tx_id,
      error_str=error_str
    )
    tx_db.abort_transaction()
    print(error_str)
    raise HTTPException(
      status_code = 500,
      detail = error_str
    )


@router.get('/procedure/{phase_key}')
async def get_phase_procedure(phase_key: str):

  db_steps = db.aql.execute(
    Queries.GET_PHASE_PROCEDURE, 
    bind_vars=dict(phase_key=phase_key)
  )

  async def get_full_step_data(step_from_db):
    step_from_db['media'] = search_step_media(step['_key'])
    return StepWithMediaInfo(**step_from_db)

  return [await get_full_step_data(step) for step in db_steps]


@router.post("/step/{step_key}/media")
async def save_step_media(
  step_key: str,
  media_file: UploadFile = File(...)
):
  
  new_media = UserFile.step_media(
    append_path=step_key,
    file=media_file,
    name=media_file.filename
  )
  
  try:
    await new_media.write_file()
  except:
    error_str = traceback.format_exc()
    status_code = 400
    response = dict(
      status=status_code,
      message='There was an error writing the file to disk',
      error_str=error_str
    )
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  return new_media.name


  

@router.delete("/step/{step_key}/media/{filename}")
async def delete_step_media(
  step_key: str,
  filename: str
):

  media_to_delete = UserFile.step_media(
    append_path=step_key,
    name=filename
  )
  
  try:
    media_to_delete.delete_file()
  except:
    error_str = traceback.format_exc()
    status_code = 400
    response = dict(
      status=status_code,
      message='There was an error deleting the file',
      error_str=error_str
    )
    raise HTTPException(
      status_code = status_code,
      detail = response
    )
