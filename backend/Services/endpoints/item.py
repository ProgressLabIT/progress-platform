import traceback

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from models.item import ProductionItem

from utils.api import APIResponse
from utils.item import *
from utils.db import db


router = APIRouter()
items_db = db.collection('ProductionItem')

@router.get('/item')
async def get_item_catalog(item_code: str = None):
  
  try: 
    item_list = [i for i in items_db.all()]
    product_list = db.aql.execute(Queries.GET_ACTIVE_PRODUCTS_FOR_BOM)

    for p in product_list:
      item_list.append(p)

  except Exception as e:
    error_str = traceback.format_exc()
    status_code = 500
    response=dict(
      status=status_code,
      message="Could not fetch data from database",
      error=error_str
    )
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  try:
    results = [ProductionItem(**p) for p in item_list]
    return results

  except Exception as e:
    error_str = traceback.format_exc()
    status_code = 500
    response=dict(
      status=status_code,
      message="There was a problem with the data fetched from the db",
      error=error_str
    )
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  