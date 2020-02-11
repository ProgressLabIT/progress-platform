from enum import Enum
from typing import List, Optional
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from pydantic import BaseModel, Field
from utils.db import db
from utils.api import APIResponse
from .models import PhaseData, PhaseSequence
import os
import traceback

router = APIRouter()

operation_db = db.collection('Operation')



@router.get('/operation')
async def get_operation_list():
  return [o for o in operation_db.all()]


@router.get("/product/{product_key}/process")
async def get_production_process(product_key):

  try:
    process_data = db.aql.execute(""" 

      LET product_id = CONCAT("Product/", @product_key)
      LET phases = DOCUMENT(product_id).process_phases

      FOR phase_id in phases
          
        LET phase = DOCUMENT(phase_id)
        LET phase_data =  MERGE(
          phase,
          { 
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
    results = [PhaseData(**phase) for phase in process_data]
    
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


@router.put("product/{product_key}/process/phase-sequence")
async def update_phase_sequence(process_phases):
  
  try:
    new_sequence = PhaseSequence(product_key, process_phases)
  except Exception as e:
    status_code = 422
    message = "The data provided doesn't match the required format"
    error_str = traceback.format_exc()
    response = {
      'status': status_code,
      'message': message,
      'error': error_str
    }
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  phase_db = db.collection('Phase')
  for phase in sequence.process_phases:
    if phase not in phase_db:
      status_code = 400
      message = f"At least one phase key is not correctly registered in the db, e.g.: { phase }"
      response = {
       'status': status_code,
       'message': message
      }
      raise HTTPException(
        status_code = status_code,
        detail = response
      )

  product_db = db.collection('Product')
  if product_key not in product_db:
    status_code = 404
    message = f"The product with key {product_key} does not exist in the database."
    response = {
      'status': status_code,
      'message': message
    }
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  try:
    product_db.update(new_sequence)
  except Exception as e:
    status_code = 500
    message = "Could not update the db"
    error_str = traceback.format_exc()
    response = {
      'status': status_code,
      'message': message,
      'error': error_str
    }
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  response_details = {
    'product_key': new_sequence.product_key,
    'process_phases': new_sequence.process_phases
  }

  return APIResponse(
    status_code = 200,
    message = "Process sequence updated",
    details = response_details
  )
