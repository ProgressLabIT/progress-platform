import traceback

from fastapi import APIRouter, HTTPException, Query

from utils.api import APIResponse
from commons.models.form import CustomField, CustomListValue, FieldType
from utils.db import db, model_to_db_dict
from utils.serial import Queries

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


@router.get('/product-steps/{product_key}')
def get_product_steps(product_key: str):
  bind_vars = dict(
    product_key = product_key
  )
  return [e for e in db.aql.execute(Queries.GET_PRODUCT_STEPS, bind_vars=bind_vars)]
