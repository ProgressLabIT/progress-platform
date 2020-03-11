from enum import Enum
from typing import List, Optional
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from utils.db import db
from utils.api import APIResponse
from utils import dt
from .models import PhaseProcedure, PhaseUpdate, Step, ProcessUpdate
from utils.file import UserFile
from fnmatch import fnmatch
import os, traceback


router = APIRouter()

operation_db = db.collection('Operation')



@router.get('/operation')
async def get_operation_list():
  return [o for o in operation_db.all()]


@router.get("/step/{step_key}/media")
async def get_step_media(step_key: str):

  step_media = UserFile.step_media(step_key)

  media_folder_exists = os.path.isdir(step_media.folder_path)

  if (media_folder_exists):
    return step_media.get_folder_contents()

  else:
    return []



@router.get("/product/{product_key}/process")
async def get_production_process(product_key):

  try:
    process_data = db.aql.execute(""" 

      LET product_id = CONCAT("Product/", @product_key)
      LET phases = DOCUMENT(product_id).process_phases

      FOR phase_id in phases
          
        LET phase = DOCUMENT(phase_id)
        LET operation_id = (
          FOR v,e IN 1..1 OUTBOUND phase_id requires
          FILTER e.type == 'PhaseOperation'
          RETURN e._to
        )[0]

        LET phase_data =  MERGE(
          phase,
          { 
            operation_id: operation_id,
            steps: DOCUMENT(phase.step_sequence)[*]
          }
        )
        RETURN phase_data

      """, bind_vars={'product_key': product_key})

  except Exception as e:
    status_code = 500
    message = "Couldn't fetch data from the db"
    error_str = traceback.format_exc()
    response = {
      'status': status_code,
      'message': message,
      'error': error_str
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )
  
  try:
    results = [PhaseProcedure(**phase) for phase in process_data]
    
  except Exception as e:
    status_code = 500
    message = "Error validating data from DB"
    error_str = traceback.format_exc()
    response = {
      'status': status_code,
      'message': message,
      'error': error_str
    }
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
        exclude_set = { 'id' } if s.id == None else None
        prepped_step_data = jsonable_encoder(s, by_alias=True, exclude=exclude_set)

        step_update = tx_db.insert_document('Step', 
          prepped_step_data, overwrite=True, return_new=True )

        phase.steps[index] = step_update['new']
        phase.step_sequence.append(step_update['_id'])

      # Flag removed steps for deletion by TTL 
      old_step_sequence = tx_db.document(phase.id)['step_sequence'] if phase.id else []
      removed_steps = [s for s in old_step_sequence if s not in phase.step_sequence]

      for r in removed_steps:
        tx_db.update_document({ '_id': r, 'trashed': timestamp })

      # Insert/replace phase
      exclude_set = { 'steps', 'operation_id' }
      # do not 'export' _id field with value null if none is set, so that the DB 
      # will set it automatically
      new_phase = True if phase.id == None else False

      if new_phase: exclude_set.add('id')
      prepped_phase_data = jsonable_encoder(phase, by_alias=True, exclude=exclude_set)
      
      phase_update = tx_db.insert_document('Phase', 
        prepped_phase_data, return_new=True, overwrite=True )
      
      new_phase_id = phase_update['_id']
      
      if new_phase:
        # Insert new ProductPhase relationship
        tx_db.insert_document('requires', {
          '_from': f'Product/{product_key}',
          '_to': new_phase_id,
          'type': 'ProductPhase'
        })

        # Insert new PhaseOperation relationship
        tx_db.insert_document('requires', {
          '_from': new_phase_id,
          '_to': phase.operation_id,
          'type': 'PhaseOperation'
        })

        process[seq].id = phase_update['_id']

      new_phase_sequence.append(new_phase_id)

    # Update new sequence, returning old one for deletion check
    phase_sequence_update = tx_db.collection('Product').update({ 
      '_key': product_key, 
      'process_phases': new_phase_sequence 
    }, return_old=True)

    # Flag removed phases (and relationships) for deletion by TTL index
    old_phase_sequence = phase_sequence_update['old']['process_phases']
    removed_phases = [p for p in old_phase_sequence if p not in new_phase_sequence]

    for p in removed_phases:
      # Flag phase document
      tx_db.update_document({ '_id': p, 'trashed': timestamp })
      
      # Flag phase relationships
      rel_flag_query = """
        FOR r IN requires 
        FILTER r._to == @phase_id || r._from == @phase_id
        UPDATE r WITH { trashed: @timestamp } IN requires
      """
      tx_db.aql.execute(rel_flag_query, bind_vars={
        'phase_id': p,
        'timestamp': timestamp
      })

    # Commit transaction
    tx_db.commit_transaction()

    return process

  except Exception as e:
    tx_id = tx_db.transaction_id
    error_str = traceback.format_exc()
    response = {
      'exception': e,
      'transaction': tx_id,
      'error_str': error_str
    }
    tx_db.abort_transaction()
    print(error_str)
    raise HTTPException(
      status_code = 500,
      detail = error_str
    )




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
    response = {
      'status': status_code,
      'message': 'There was an error writing the file to disk',
      'error_str': error_str
    }
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
    response = {
      'status': status_code,
      'message': 'There was an error deleting the file',
      'error_str': error_str
    }
    raise HTTPException(
      status_code = status_code,
      detail = response
    )
