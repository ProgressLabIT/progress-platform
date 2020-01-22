from typing import List, Optional
from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from pydantic import BaseModel, Field
from .db import db
import os
import traceback
router = APIRouter()

operation_db = db.collection('Operation')

@router.get('/operation')
async def get_operation_list():
  return [o for o in operation_db.all()]