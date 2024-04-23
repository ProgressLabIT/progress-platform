import traceback

from fastapi import APIRouter, HTTPException, Query

from utils.api import APIResponse
from models.form import CustomField, CustomListValue, FieldType
from utils.db import db, model_to_db_dict

router = APIRouter()

@router.get('/serial-field')
def fetch_field(name: str | None = None, key: str | None = None):
  match = dict()
  if name:
    match['name'] = name
  if key:
    match['_key'] = key
  match['use_in_serial'] = True
  cursor = db.collection('CustomField').find(match)
  result = [CustomField(**f) for f in cursor]
  return sorted(result, key=lambda x: x.name.lower())
