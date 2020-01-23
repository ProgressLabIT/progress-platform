from typing import List, Optional
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from pydantic import BaseModel, Field
from utils.db import db
from utils.api import APIResponse

import os
import traceback

router = APIRouter()

class Step(BaseModel):
  key: str = Field(..., alias="_key")
  title: str
  description: str = None
  type: str

class PhaseData(BaseModel):
  sequence: int
  operation: str
  steps: List[Step] = []


operation_db = db.collection('Operation')

@router.get('/operation')
async def get_operation_list():
  return [o for o in operation_db.all()]





@router.get("/product/{product_key}/process")
async def get_production_process(product_key):

  try:
    process_data = db.aql.execute("""

        FOR v1, e1 IN 1..1 OUTBOUND CONCAT('Product/', @product_key) requires
        FILTER e1.type == 'ProductPhase'
        SORT e1.sequence
        LET phase_data =  
          {
            sequence: e1.sequence,
            operation: (
                FOR v2,e2 IN OUTBOUND Document(e1._to) requires
                FILTER e2.type == 'PhaseOperation'
                RETURN v2.name)[0],
            steps: (
                FOR step IN Step
                FILTER step.phase_id == v1._key
                SORT step.sequence
                RETURN { 
                  _key: step._key,
                  title: step.title, 
                  description: step.description,
                  type: step.type
                  }
                )
          }
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
