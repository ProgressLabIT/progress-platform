import traceback

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .models import ProductionItem

from utils.api import APIResponse
from utils.db import db


router = APIRouter()
items_db = db.collection('ProductionItem')

@router.get('/item')
async def get_bom_catalog(item_code: str = None):
  
  try: 
    item_list = [i for i in items_db.all()]
    product_list = db.aql.execute("""
      FOR p IN Product
      RETURN {
        type: 'subassembly',
        _id: p._id,
        code: p.code,
        description: p.description
      }
    """)

    for p in product_list:
      item_list.append(p)

  except Exception as e:
    error_str = traceback.format_exc()
    status_code = 500
    response = {
      "status": status_code,
      "message": "Could not fetch data from database",
      "error": error_str
    }
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
    response = {
      "status": status_code,
      "message": "There was a problem with the data fetched from the db",
      "error": error_str
    }
    raise HTTPException(
      status_code = status_code,
      detail = response
    )

  