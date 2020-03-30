from utils.db import db
from utils.api import APIResponse
from fastapi import APIRouter, UploadFile, HTTPException, Form, File, Body
from fastapi.encoders import jsonable_encoder
from typing import List
from .models import UserCredentials, User

import json

import os, traceback



router = APIRouter()

@router.post("/user-session")
async def start_user_session(user: UserCredentials):

  try:
    user = db.collection('User').find(jsonable_encoder(user)).next()
  
  except Exception as e:
    status_code = 401
    response = {
      "status": status_code,
      "message": "Nome utente o password sbagliati"
    }
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  return User(**user.dict())



@router.get("/user")
async def get_user_list():

  user_list = [User(**u) for u in db.collection('User').find({ 'active': True })]

  return APIResponse(detail=user_list)