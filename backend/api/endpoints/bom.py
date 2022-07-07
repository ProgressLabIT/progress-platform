import json
import os
import requests
import traceback
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder

from models.bom import *
from utils.bom import *
from utils.db import db
from utils.api import APIResponse



router = APIRouter()




@router.get("/{product_key}/bom")
async def get_product_bom(product_key):
  try: 
    bom = get_bom_from_db(db, product_key)
    return bom

  except Exception as e:
    status_code = 500
    error_str = traceback.format_exc()
    response=dict(
      status=status_code,
      message="There was a problem fetching the data from the db",
      error=error_str 
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


@router.put('/{product_key}/bom')
async def update_bom(product_key: str, new_bom: List[BomLineWriteIn]):
  """
  First draft will blatantly delete existing bom and
  replace it with the new one
  """

  # Begin transaction
  txn = db.begin_transaction(write="requires")
  
  try:

    # Remove old bom
    deleted_items = txn.aql.execute(
      Queries.DELETE_PRODUCT_BOM, 
      bind_vars=dict(product_key=product_key)
    )
    # print("Deleted items: ", [i for i in deleted_items])

    # Enrich data
    bom_to_db = [define_bom_line_for_db(line) for line in new_bom]
    print(bom_to_db)
    # Insert new bom
    txn.collection('requires').insert_many(bom_to_db, silent=True)    
    txn.commit_transaction()
    
    return APIResponse(message="BoM updated correctly")

  except Exception as e:
    error_str = traceback.format_exc()
    status_code = 500

    response=dict(
      status=status_code,
      message="There was a problem updating the bom. Transaction has been aborted.",
      error=error_str 
    )
    print("Error! Aborting transaction...")
    txn.abort_transaction()
    print(error_str)
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


