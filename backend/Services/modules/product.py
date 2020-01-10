from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from .db import db

router = APIRouter()


class Product(BaseModel):
  """ 
  Represents the subset of the Product DB schema necessary 
  for use in the product list view
  """

  # the _key field must be aliased because pydantic will not 
  # accept fields with leading underscore
  key: str = Field(..., alias="_key")
  code: str
  description: Optional[str] = None
  active: bool = True



@router.get("/")
async def get_product_list(
  limit: int = None, # return a limited number of results
  code: str = None, # filter by code
):

  list =  db.aql.execute("""
    LET search = CONCAT('%', @code, '%')
    FOR p IN Product
      FILTER !p.trash && LIKE(p.code, search, true)
      LIMIT @limit
      RETURN p
    """, bind_vars={"code": code, "limit": limit})

  results = [Product(**p) for p in list]
  return results


