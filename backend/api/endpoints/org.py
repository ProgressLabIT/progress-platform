import secrets
import traceback
from typing import List

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, Request, Depends
from utils import auth
from starlette import status

from models.org import *
from utils import auth
from utils.api import APIResponse, AuthAPIResponse
from utils.db import db
from utils.file import FileHandler
from utils.org import *
from models.auth import TokenData, TokenRecord, AuthResponse, TokenContext
from starlette.responses import JSONResponse
from fastapi.encoders import jsonable_encoder



from managers.server_event_manager import ServerEventManager
from sse_starlette.sse import EventSourceResponse

ACCESS_TOKEN_EXPIRE_MINUTES = 52596000 # 100 years



router = APIRouter()


# =================================
#         DEPARTMENTS
# =================================
@router.get('/department',
    dependencies=[Depends(auth.verify_token)])
async def get_department_list():
  dep_list = [Department(**dep) for dep in db.collection('Department').all()]
  response = APIResponse(detail= dep_list)
  return response


# =================================
#         API TOKEN
# =================================
@router.get("/api-token")
async def get_api_token(token_description: str, token_expiration: datetime, user_token: TokenData = Depends(auth.verify_token)):
  credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
  try:
    user_key=user_token.consumer_key
    if user_key is None:
      raise credentials_exception

    user = User( **db.collection('User').get(user_key) )

    token, token_data = auth.issue_token(
      consumer_key = user_token.consumer_key,
      expiration_date=token_expiration,
      scope = user.scope,
    )

    response_data = AuthResponse(
      action='api_token',
      user_key=user_key
    )

    # Store token data
    _, _, token_signature = token.split('.')

    token_record = TokenRecord(
      key=token_data.token_key,
      issued_to=user.id,
      issued_at=token_data.issued_at,
      expires_at=token_data.expires_at,
      context=TokenContext.API,
      signature=token_signature,
      description=token_description
    )
    db.collection('Token').insert(token_record)


    response_headers = {
      'Cache-Control': 'no-store',
      'Pragma': 'no-cache'
    }

    response_content = AuthAPIResponse(detail=response_data)

    response_content.access_token = token
    response_content.token_type = "bearer"
    return JSONResponse(
      content= jsonable_encoder(response_content),
      headers=response_headers
    )
  except:
    raise credentials_exception


@router.delete("/api-token/{token}",
    dependencies=[Depends(auth.verify_token)])
async def revoke_token(token: str):
    try:
      auth.revoke_token(token)
      return APIResponse(message="token deleted correctly")
    except:
      raise HTTPException(status_code=500, detail="Cannot delete token")


# =================================
#         USERS
# =================================
@router.get("/user",
    dependencies=[Depends(auth.verify_token)])
async def get_user_list(active_only: bool = True):

  db_cursor = db.aql.execute(Queries.GET_USER_LIST, bind_vars=dict(active_only=active_only))
  user_list = [UserListItem(**u) for u in db_cursor]

  return APIResponse(detail=user_list)

# ----------------------------------------------------

@router.post("/user", status_code=201,
    dependencies=[Depends(auth.verify_token)])
async def create_user(new_user: UserNew):
  new_user_data = User(**new_user.model_dump())
  username_already_taken = db.collection('User').find(dict(username=new_user.username)).count()

  if username_already_taken:
    raise HTTPException(status_code=409, detail="A user with the provided username already exists")

  temp_psw = secrets.token_hex(4)
  new_user_data.psw_hash = auth.get_password_hash(temp_psw)
  new_user_data.reset_password = True

  new_user_record = db.collection('User').insert(new_user_data, return_new=True)['new']
  response_data = dict(temp_psw=temp_psw)
  return APIResponse(status_code=201, message='User created', detail=response_data)

# ----------------------------------------------------

@router.patch("/user/{user_key}",
    dependencies=[Depends(auth.verify_token)])
async def update_user(user_key: str, update_data: dict):

  user_update = dict(_key=user_key)
  user_model_fields = User.schema()['properties']
  for k,v in update_data.items():
    if k in user_model_fields:
      user_update[k] = v
    else:
      raise HTTPException(
        status_code=422,
        detail='Incorrect data. Please review API specs for allowed fields.'
      )

  try:
    db_update = db.collection('User').update(user_update, return_new=True)['new']
    updated_user = UserListItem(**db_update)
    return APIResponse(message='User updated', detail=updated_user)

  except:
    response = dict(
      message="Could not update data in the database",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=500,
      detail=response
    )

# ----------------------------------------------------

@router.put("/user/{user_key}/image",
    dependencies=[Depends(auth.verify_token)])
async def update_user_image(
  user_key: str,
  new_image: UploadFile = File(...)
):
  # TODO: OBJECT STORAGE MIGRATION - Upload user image to object storage
  try:
    user = User(**db.collection('User').get(user_key))
    img = FileHandler.user_image(file=new_image)
    filename = (user.name + user.surname + '.jpg').replace(' ', '').lower()
    await img.write_file(custom_name=filename)
    return APIResponse(message="File saved correctly")
  except Exception:
    raise HTTPException(
      status_code = 500,
      detail = dict(
        message = "Could not save image to disk",
        error = traceback.format_exc()
      )
    )

# ----------------------------------------------------

@router.delete("/user/{user_key}/password",
    dependencies=[Depends(auth.verify_token)])
async def delete_user_password(user_key: str):
  try:
    temp_psw = secrets.token_hex(4)
    new_hash = auth.get_password_hash(temp_psw)
    db.collection('User').update(dict(_key=user_key, psw_hash=new_hash, reset_password=True))
    return APIResponse(message="Password updated correctly", detail=dict(temp_psw=temp_psw))

  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="There was an error updating the password, please contact the administrator.",
      error=traceback.format_exc(),
    )
    raise HTTPException(status_code=status_code, detail=response)

# ----------------------------------------------------

@router.put("/user/{user_key}/password",
    dependencies=[Depends(auth.verify_token)])
async def reset_user_password(
  user_key: str,
  token: str = Depends(auth.verify_token),
  new_password: str = Body(..., embed=True)
):
  if not user_key == token.consumer_key:
    raise auth.credentials_exception

  try:
    new_hash = auth.get_password_hash(new_password)
    db.collection('User').update(dict(_key=user_key, psw_hash=new_hash, reset_password=False))
    return APIResponse(message="Password updated correctly")

  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="There was an error updating the password, please contact the administrator.",
      error=traceback.format_exc(),
    )
    raise HTTPException(status_code=status_code, detail=response)

# ----------------------------------------------------

@router.get("/user/api-tokens",
    dependencies=[Depends(auth.verify_token)])
async def get_user_api_tokens(
  token: str = Depends(auth.verify_token),
):
  user_key=token.consumer_key
  if not user_key == token.consumer_key:
    raise auth.credentials_exception

  try:
    user = User( **db.collection('User').get(user_key) )
    cursor = db.collection('Token').find(dict(
        issued_to=user.id,
        revoked=False,
        context=TokenContext.API
      ))
    return [TokenRecord(**t) for t in cursor]

  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="There was an error retreiving the api tokens.",
      error=traceback.format_exc(),
    )
    raise HTTPException(status_code=status_code, detail=response)

# ----------------------------------------------------

@router.delete("/user/{user_key}",
    dependencies=[Depends(auth.verify_token)])
async def archive_user(user_key: str):
  try:
    db.collection('User').update(dict(_key=user_key, trash=True))
    return APIResponse(message="User archived successfully", detail=dict(user_key=user_key))

  except:
    status_code = 500
    response = dict(
      status=status_code,
      message="There was an error while updating the user, please contact the administrator reporting the following error description.",
      error=traceback.format_exc(),
    )
    raise HTTPException(status_code=status_code, detail=response)

@router.get("/notification/{topic}")
async def message_stream(request: Request, topic: str):
    return EventSourceResponse(ServerEventManager.getInstance().push_events(request, topic))


