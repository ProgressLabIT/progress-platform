from utils.db import db
from utils.api import APIResponse
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from fastapi.encoders import jsonable_encoder
from typing import List
from .models import BomItemRead, BomItemWrite
import json

import os, traceback


router = APIRouter()

@router.get("/{product_key}/bom")
async def get_product_bom(product_key):
  try: 
    bom = db.aql.execute("""
      FOR v,e IN 2..2 OUTBOUND @product requires
      FILTER e.rel_type like 'BomItem'
      LET phase = e._from
      
      RETURN {
          item_id: v._id,
          rel_id: e._id,
          code: v.code,
          description: v.description,
          type: v.type,
          phase_id: phase,
          phase_name: DOCUMENT(phase).alias,
          qt: e.qt
      }
    """, bind_vars={ 'product': f'Product/{product_key}' })


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
  
  try:
    results = [BomItemRead(**i) for i in bom]
    return results

  except Exception as e:
    status_code = 500
    error_str = traceback.format_exc()
    response = {
      "status": status_code,
      "message": "There was a problem with the data fetched from the db",
      "error": error_str 
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


@router.put('/{product_key}/bom')
async def update_bom(product_key: str, new_bom: List[BomItemWrite]):
  """
  First draft will blatantly delete existing bom and
  replace it with the new one
  """

  # Begin transaction
  txn = db.begin_transaction(write="requires")
  
  try:

    # Remove old bom
    deleted_items = txn.aql.execute("""
      FOR v,e IN 2..2 OUTBOUND @product requires
      FILTER e.rel_type=="BomItem"
      REMOVE e IN requires
    """, bind_vars={ "product": f'Product/{product_key}'})
    print("Deleted items: ", [i for i in deleted_items])

    # Insert new bom
    def insert_item(txn, item):
      prepped_item = jsonable_encoder(item, include_none=False)
      print(prepped_item)
      return txn.collection('requires').insert(prepped_item, return_new=True)

    saved_bom = [ insert_item(txn, i) for i in new_bom ]
    
    print(saved_bom)

    # Commit transaction
    txn.commit_transaction()
    print("Transaction committed!")
    return saved_bom

  except Exception as e:
    print("Error!")
    error_str = traceback.format_exc()
    status_code = 500
    print("Setting response...")

    response = {
      "status": status_code,
      "message": "There was a problem updating the bom. Transaction has been aborted.",
      "error": error_str 
    }
    print("Aborting transaction...")
    txn.abort_transaction()
    print("Transaction aborted. Raising exception...")
    print(error_str)
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


