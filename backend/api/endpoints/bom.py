import json
import os
import requests
import traceback
from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from fastapi.encoders import jsonable_encoder

from models.bom import *
from models.product import ProductFull
from utils.api import APIResponse
from utils.bom import *
from utils.db import db
from utils.api import APIResponse
from utils.product import get_product_data_from_code
from utils import auth



router = APIRouter()

@router.get("/{product_key}/bom",
    response_model=list,
    responses={500: {"description": "Database query error fetching BoM"}},
    dependencies=[Depends(auth.verify_token)])
async def get_product_bom(product_key: str):
  """Retrieve the Bill of Materials for a product.

  Returns an ordered list of `BomLineRead` objects for `product_key`, each
  including component code, description, quantity, phase assignment, and
  consumption options.

  **Emits:** *(direct query — no event class)*

  **Required scope:** `product:bom:read`
  """
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




@router.put('/{product_key_or_code}/bom',
    response_model=APIResponse,
    responses={
      401: {"description": "Product not found by key"},
      403: {"description": "BoM update would create a circular component dependency"},
      422: {"description": "Product has no production process — BoM cannot be assigned"},
      500: {"description": "Transaction error during BoM replace"},
    },
    dependencies=[Depends(auth.verify_token)])
async def update_bom(
  product_key_or_code: str,
  new_bom: List[BomLineWriteIn],
  by_code: bool = False
  ):
  """Replace the Bill of Materials for a product.

  Performs a full replace: the existing BoM is deleted and `new_bom` is
  inserted atomically within a single transaction. Pass `by_code=true` to
  resolve `product_key_or_code` as a product code rather than an ArangoDB key.

  - Lines without an explicit `phase_key` are assigned to the product's last
    phase.
  - After insert, a loop-detection query runs; if circular dependencies are
    found the transaction is aborted and HTTP 403 is returned with the loop data.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `product:bom:update`
  """

  # Allow external tools to use item codes instead of db _keys
  if by_code:
    product = get_product_data_from_code(product_key_or_code)

  else:
    try:
      product = ProductFull(**db.collection('Product').get(product_key_or_code))
    except StopIteration:
      raise HTTPException(
        status_code=401,
        detail=f"Could not find product with key {product_key_or_code}"
      )

  try:
    last_phase = product.process_phases[-1]
  except IndexError:
    raise HTTPException(
      status_code=422,
      detail=f"Product must have a production process to have a BoM"
    )
  for bom_line in new_bom:
    # Fetch component key if necessary
    if by_code:
      component_data = get_product_data_from_code(bom_line.component_code)
      bom_line.component_key = component_data.key

    # Assign line to last phase if none is indicated
    if bom_line.phase_key == None:
      bom_line.phase_key = last_phase

  """
  First draft will blatantly delete existing bom and
  replace it with the new one
  """

  # Begin transaction
  tx = db.begin_transaction(write="requires")

  try:

    # Remove old bom
    deleted_items = tx.aql.execute(
      Queries.DELETE_PRODUCT_BOM,
      bind_vars=dict(product_key=product.key)
    )

    bom_to_db = [define_bom_line_for_db(line) for line in new_bom]

    # Insert new bom
    tx.collection('requires').insert_many(bom_to_db, silent=True)

  except Exception as e:
    tx.abort_transaction()
    error_str = traceback.format_exc()
    status_code = 500
    response=dict(
      status=status_code,
      message="There was a problem updating the bom. Transaction has been aborted.",
      error=error_str
    )
    tx.abort_transaction()
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  # Check for loops in BoM relationships
  bom_loops = find_bom_loops(db=tx, product_key=product.key)

  if not len(bom_loops):
    tx.commit_transaction()
    return APIResponse(message="BoM updated correctly")

  else:
    tx.abort_transaction()
    status_code = 403
    response=dict(
      status = status_code,
      message = "Bom contains loops: at least one of the component requires the current product to be built.",
      data = bom_loops
    )
    raise HTTPException(
      status_code = status_code,
      detail = response
    )
