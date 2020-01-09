from fastapi import APIRouter
from pydantic import BaseModel
from .db import db

router = APIRouter()


class Product(BaseModel):
  code: str
  description: str



@router.get("/")
async def get_product_list(max: int = 0, search: str = None):
  limit = max if max else None
  list = db.collection('Product').all(limit=limit)
  # search/filtering termporarily implemented only at the client level
  return [product for product in list]



