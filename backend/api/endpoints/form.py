from fastapi import APIRouter, HTTPException

from utils.api import APIResponse
from models.form import CustomField, CustomListValue
from utils.db import db

router = APIRouter()


@router.post('/field')
def create_field(field_data: CustomField):
  field_key = db.collection('CustomField').insert(field_data)['_key']
  return APIResponse(
    message = "Field created successfully",
    detail = dict(field_key=field_key)
  )


@router.get('/field')
def fetch_field(name: str = None, key: str = None):
  match = dict()
  if name:
    match['name'] = name
  if key:
    match['_key'] = key

  cursor = db.collection('CustomField').find(match)
  return [CustomField(**f) for f in cursor]



@router.get('/list')
def fetch_custom_list_values(field_key: str):
  match = dict(field_key=field_key)
  return [CustomListValue(**v) for v in db.collection('CustomListValue').find(match)]



