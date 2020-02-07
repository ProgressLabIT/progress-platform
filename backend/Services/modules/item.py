from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from utils.db import db
from utils.api import APIResponse
from .models import ProductionItem
import traceback


router = APIRouter()
items_db = db.collection('ProductionItem')

@router.get('/item')
async def get_item_catalog(item_code: str = None):
  
  try: 
    item_list = items_db.all()

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

  