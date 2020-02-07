from enum import Enum
from typing import List, Optional
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from pydantic import BaseModel, Field
from utils.db import db
from utils.api import APIResponse
from .models import PhaseData
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

        LET phases = (
          FOR p in Product
          FILTER p._key == @product_key
          RETURN p.process_phases
          )[0]

        FOR phase_key in phases
          LET phase_data =  MERGE(
            DOCUMENT(CONCAT('Phase/', phase_key)),
            { 
              steps: (
                  FOR step IN Step
                  FILTER step.phase_id == phase_key
                  SORT step.sequence
                  RETURN step
              )
            })
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
