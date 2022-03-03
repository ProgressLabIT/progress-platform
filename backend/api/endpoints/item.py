import traceback

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from models.item import ProductionItem

from utils.api import APIResponse
from utils.item import *
from utils.db import db

import logger as log

router = APIRouter()
items_db = db.collection('ProductionItem')

loggy = log.get_logger(__name__)

@router.get('/item')
async def get_item_catalog(item_code: str = None):
  '''
  Method to fetch all production items and active products from the database.
  Returns:
    1. a list of ProductionItem objects, and 200 status code in nominal operations
    2. traceback and 500 status code when data can not be fetched from the database or data is invalid
  '''
  
  try: 
    item_list = [i for i in items_db.all()]
    product_list = db.aql.execute(Queries.GET_ACTIVE_PRODUCTS_FOR_BOM)

    for p in product_list:
      item_list.append(p)

  except Exception as e:
    msg = "Could not fetch data from database"
    error_str = traceback.format_exc()
    status_code = 500
    response=dict(
      status=status_code,
      message=msg,
      error=error_str
    )
    loggy.error(msg)
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  try:
    results = [ProductionItem(**p) for p in item_list]
    return results

  except Exception as e:
    msg = "There was a problem with the data fetched from the db"
    error_str = traceback.format_exc()
    status_code = 500
    response=dict(
      status=status_code,
      message=msg,
      error=error_str
    )
    loggy.error(msg)
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  