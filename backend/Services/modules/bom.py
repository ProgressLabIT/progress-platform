from utils.db import db
from utils.api import APIResponse

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, UploadFile, HTTPException, Form, File

import os, traceback


router = APIRouter()

class BomItem(BaseModel):
  key: str = Field(..., alias="_key")
  code: str
  description: str
  type: str
  phase_seq: int = None
  operation: str = None
  qt = 0




@router.get("/{product_key}/bom")
async def get_product_bom(product_key):
  try: 
    bom = db.aql.execute("""
      FOR v,e,p IN 1..2 OUTBOUND @product requires

      FILTER v._id like 'ProductionItem/%'
      
      /*  check if last edge to ProductionItem started from Phase or directly from Product
          if yes, get the phase sequence from the ProductPhase relationship, which
          is the first of the two edges of the path.
          
          (this might be simplified storing the sequence on the Phase document
          rather than in its relationship to the product)
      */
      LET phase_seq = e._from like 'Phase/%' ? p.edges[0].sequence : null 
      
      RETURN {
          _key: v._key,
          code: v.code,
          description: v.description,
          type: v.type,
          phase_seq: phase_seq,
          // get operation name
          operation: (FOR op, r in 1..1 OUTBOUND DOCUMENT(e._from) requires FILTER r.type == 'PhaseOperation' RETURN op.description)[0]
          // missing the required quantity: not stored in the test data
      }
    """, bind_vars={ 'product': f'Product/{product_key}' })

    results = [BomItem(**i) for i in bom]

    return results

  except Exception as e:
    status_code = 500
    error_str = traceback.format_exc()
    response = {
      "status": status_code,
      "message": "Couldn't fetch bom from db",
      "error": error_str 
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )