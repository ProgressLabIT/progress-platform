from typing import List
from fastapi import APIRouter, HTTPException
from utils.api import APIResponse
from utils.db import db
import traceback
from .models import Department

router = APIRouter()

@router.get('/department')
async def get_department_list():
  dep_list = [Department(**dep) for dep in db.collection('Department').all()]
  response = APIResponse(detail= dep_list)
  return response