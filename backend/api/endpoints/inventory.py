import traceback

from fastapi import APIRouter, HTTPException, Query, Depends
from utils import auth

from utils.api import APIResponse
from models.inventory import *
from utils.db import db, model_to_db_dict

router = APIRouter()


@router.get('/position')
def get_positions(
  search: str | None = None,
  has_product_keys: list[str] | None = None,
  limit: int | None = 200,
  offset: int | None = 0,
  is_in_position: str | None = None,
  contains_position: str | None = None
):
  ...



@router.get('/position/{position_key}')
def get_position_contents(position_key):
  ...



@router.post('/position')
def create_position(new_position: Position):
  ...


@router.delete('/position/{position_key}')
def delete_position(position_key):
  ...


@router.get('/movement')
def search_inventory_journal(
  datetime_from: date | None = None,
  datetime_to: date | None = None,
  product_key: str | None = None,
  product_code: str | None = None,
  through_position_key: str | None = None,
  through_position_code: str | None = None,
  include_related_positions: bool | None = True,
  movement_type: InventoryMovementType | None = None,
):
  ...



@router.get('/mission')
def search_warehouse_missions(
  search: str | None = None, # searches the mission code and references
  includes_product_key: str | None = None,
  includes_product_code: str | None = None,
  due_by_min: date | None = None,
  due_by_max: date | None = None,
  status: MovementStatus | None = None,
):
  ...


@router.get('/mission/{mission_key}')
def get_warehouse_mission_details(mission_key):
  # Must include data about all the related movements
  ...
