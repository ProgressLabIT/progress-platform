from utils.db import db
from utils.api import APIResponse
from fastapi import APIRouter, UploadFile, HTTPException, Form, File, Body
from fastapi.encoders import jsonable_encoder
from typing import List
from .user_m import UserCredentials, User

import json

import os, traceback



router = APIRouter()

@router.post("/user-session")
async def start_user_session(user: UserCredentials):

  print(user)

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

  return user