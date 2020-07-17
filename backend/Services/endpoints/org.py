import secrets
import traceback
from typing import List

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from starlette import status

from models.org import *
from utils import auth
from utils.api import APIResponse
from utils.db import db
from utils.file import UserFile



router = APIRouter()


# =================================
#         DEPARTMENTS
# =================================
@router.get('/department')
async def get_department_list():
  dep_list = [Department(**dep) for dep in db.collection('Department').all()]
  response = APIResponse(detail= dep_list)
  return response



# =================================
#         USERS
# =================================
@router.get("/user")
async def get_user_list(active_only: bool = True):

  query = """
    FOR u IN User
    LET active_filter = @active_only ? 'true' : '%'
    FILTER LIKE(TO_STRING(u.active), active_filter) && !u.trash
    SORT u.surname, u.name
    LET dep_data = DOCUMENT(u.department_id)
    LET last_login = DOCUMENT(u.last_user_session).start
    RETURN MERGE(u, { department: dep_data }, { last_login })
  """

  # user_list = [User(**u) for u in db.collection('User').find({ 'active': True })]
  db_cursor = db.aql.execute(query, bind_vars={ 'active_only': active_only })
  user_list = [UserListItem(**u) for u in db_cursor]
  
  return APIResponse(detail=user_list)

# ----------------------------------------------------

@router.post("/user", status_code=201)
async def create_user(new_user: UserNew):
  new_user_data = User(**new_user.dict()) 
  username_already_taken = db.collection('User').find({ 'username': new_user.username }).count()

  if username_already_taken:
    raise HTTPException(status_code=409, detail="A user with the provided username already exists")

  temp_psw = secrets.token_hex(4)
  new_user_data.psw_hash = auth.get_password_hash(temp_psw)
  new_user_data.reset_password = True

  new_user_record = db.collection('User').insert(new_user_data, return_new=True)['new']
  response_data = dict(temp_psw=temp_psw)
  return APIResponse(status_code=201, message='User created', detail=response_data)
    
# ----------------------------------------------------

@router.patch("/user/{user_key}")
async def update_user(user_key: str, update_data: dict):

  user_update = { '_key': user_key }
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
    response = {
      'message': "Could not update data in the database",
      'error': traceback.format_exc()
    }
    raise HTTPException(
      status_code=500,
      detail=response
    )

# ----------------------------------------------------

@router.put("/user/{user_key}/image")
async def update_user_image(
  user_key: str, 
  new_image: UploadFile = File(...)
):
  user = User(**db.collection('User').get(user_key))
  img = UserFile.user_image(file=new_image)
  filename = (user.name + user.surname + '.jpg').replace(' ', '').lower()
  await img.write_file(filename)  
  return APIResponse(message="File saved correctly")

# ----------------------------------------------------

@router.delete("/user/{user_key}/password")
async def delete_user_password(user_key: str):
  try:
    temp_psw = secrets.token_hex(4)
    new_hash = auth.get_password_hash(temp_psw)
    db.collection('User').update({ '_key': user_key, 'psw_hash': new_hash, 'reset_password': True })
    return APIResponse(message="Password updated correctly", detail={ 'temp_psw': temp_psw })

  except: 
    status_code = 500
    response = {
      'status': status_code,
      'message': "There was an error updating the password, please contact the administrator.",
      'error': traceback.format_exc(),
    }
    raise HTTPException(status_code=status_code, detail=response)

# ----------------------------------------------------

@router.put("/user/{user_key}/password")
async def reset_user_password(
  user_key: str, 
  token: str = Depends(auth.verify_token),
  new_password: str = Body(..., embed=True)
):
  print(new_password)
  if not user_key == token.consumer_key:
    raise auth.credentials_exception

  try:
    new_hash = auth.get_password_hash(new_password)
    db.collection('User').update({ '_key': user_key, 'psw_hash': new_hash, 'reset_password': False })
    return APIResponse(message="Password updated correctly")

  except: 
    status_code = 500
    response = {
      'status': status_code,
      'message': "There was an error updating the password, please contact the administrator.",
      'error': traceback.format_exc(),
    }
    raise HTTPException(status_code=status_code, detail=response)

# ----------------------------------------------------

@router.delete("/user/{user_key}")
async def archive_user(user_key: str):
  try:
    db.collection('User').update({ '_key': user_key, 'trash': True })
    return APIResponse(message="User archived successfully", detail={ 'user_key': user_key })
    
  except:
    status_code = 500
    response = {
      'status': status_code,
      'message': "There was an error while updating the user, please contact the administrator reporting the following error description.",
      'error': traceback.format_exc(),
    }
    raise HTTPException(status_code=status_code, detail=response)


