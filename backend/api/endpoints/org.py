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




ACCESS_TOKEN_EXPIRE_MINUTES = 52596000 # 100 years



router = APIRouter()


# =================================
#         DEPARTMENTS
# =================================
@router.get(
  '/department',
  response_model=APIResponse,
  responses={},
  dependencies=[Depends(auth.verify_token)],
)
async def get_department_list():
  """Return the list of all departments.

  Fetches every document from the `Department` collection and returns them
  wrapped in an `APIResponse`. No filtering is applied; results include
  all departments regardless of active status.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:department:read`
  """
  dep_list = [Department(**dep) for dep in db.collection('Department').all()]
  response = APIResponse(detail= dep_list)
  return response


# =================================
#         API TOKEN
# =================================
@router.get(
  "/api-token",
  response_model=AuthAPIResponse,
  responses={
    401: {"description": "Invalid or missing session token"},
    500: {"description": "Unexpected error during token issuance or storage"},
  },
)
async def get_api_token(token_description: str, token_expiration: datetime, user_token: TokenData = Depends(auth.verify_token)):
  """Issue a long-lived API token for the calling user.

  Creates a new JWT with context `API` scoped to the caller's permissions,
  stores the token signature in the `Token` collection, and returns the
  signed token in an `AuthAPIResponse`. The token's expiry is set to
  `token_expiration`. Useful for server-to-server integrations and automation
  scripts that cannot perform interactive login.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:api-token:create`
  """
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


@router.delete(
  "/api-token/{token_key}",
  response_model=APIResponse,
  responses={
    500: {"description": "Error while revoking the token record"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def revoke_token(token_key: str):
  """Revoke an API token by key.

  Marks the `Token` document identified by `token_key` as revoked so that
  subsequent requests bearing that JWT are rejected. The token document
  is not deleted — the revocation state is persisted for audit purposes.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:api-token:revoke`
  """
  try:
    auth.revoke_token(token_key)
    return APIResponse(message="token deleted correctly")
  except:
    raise HTTPException(status_code=500, detail="Cannot delete token")


# =================================
#         USERS
# =================================
@router.get(
  "/user",
  response_model=APIResponse,
  responses={},
  dependencies=[Depends(auth.verify_token)],
)
async def get_user_list(active_only: bool = True):
  """Return a list of users, optionally filtered to active accounts.

  Executes `Queries.GET_USER_LIST` with the `active_only` flag. Each result
  is a `UserListItem` that includes department details and login state. Pass
  `active_only=false` to include archived/disabled accounts.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:user:read`
  """

  db_cursor = db.aql.execute(Queries.GET_USER_LIST, bind_vars=dict(active_only=active_only))
  user_list = [UserListItem(**u) for u in db_cursor]

  return APIResponse(detail=user_list)

# ----------------------------------------------------

@router.post(
  "/user",
  status_code=201,
  response_model=APIResponse,
  responses={
    409: {"description": "A user with the provided username already exists"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def create_user(new_user: UserNew):
  """Create a new platform user with a temporary password.

  Validates that the `username` is not already taken, generates a random
  8-character hex temporary password, hashes it, and inserts the `User`
  document with `reset_password=True`. The plain-text temporary password
  is returned in `detail.temp_psw` — it is not stored. The user must
  change it on first login.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:user:create`
  """
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

@router.patch(
  "/user/{user_key}",
  response_model=APIResponse,
  responses={
    422: {"description": "Request body contains a field not present in the User model"},
    500: {"description": "Database error during user update"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def update_user(user_key: str, update_data: dict):
  """Partially update a user document.

  Accepts a flat JSON object. Only keys that exist in the `User` model
  schema are applied; any unrecognised field causes a 422 rejection. The
  update is performed as a direct collection update (no transaction).

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:user:write`
  """

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

@router.put(
  "/user/{user_key}/image",
  response_model=APIResponse,
  responses={
    500: {"description": "Filesystem error while saving the uploaded image"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def update_user_image(
  user_key: str,
  new_image: UploadFile = File(...)
):
  """Upload or replace a user's profile image.

  Reads the existing `User` document to derive a filename
  (`{name}{surname}.jpg` in lowercase), then writes the image to the
  configured file storage path via `FileHandler.user_image`. Replaces any
  previously stored image for the same user.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:user:write`
  """
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

@router.delete(
  "/user/{user_key}/password",
  response_model=APIResponse,
  responses={
    500: {"description": "Database error during password hash replacement"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def delete_user_password(user_key: str):
  """Reset a user's password to a new random temporary value.

  Generates a new random 8-character hex password, hashes it, updates the
  `User` document with `reset_password=True`, and returns the plain-text
  temporary password in `detail.temp_psw`. The user must change it on next
  login. Used by admins to unlock accounts when users forget their password.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:user:write`
  """
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

@router.put(
  "/user/{user_key}/password",
  response_model=APIResponse,
  responses={
    401: {"description": "Token consumer key does not match the user_key path parameter"},
    500: {"description": "Database error during password hash update"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def reset_user_password(
  user_key: str,
  token: str = Depends(auth.verify_token),
  new_password: str = Body(..., embed=True)
):
  """Set a new password for the calling user (post-reset flow).

  Validates that `user_key` matches the JWT's `consumer_key` — users can
  only reset their own password via this endpoint. Hashes `new_password`
  and clears the `reset_password` flag. Intended to be called after a
  forced password reset triggered by `POST /auth` returning `action=reset_password`.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `auth:password:reset`
  """
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

@router.get(
  "/user/api-tokens",
  response_model=list[TokenRecord],
  responses={
    401: {"description": "Token consumer key validation failed"},
    500: {"description": "Database error while fetching token records"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def get_user_api_tokens(
  token: str = Depends(auth.verify_token),
):
  """Return all non-revoked API tokens belonging to the calling user.

  Queries the `Token` collection filtered by `issued_to` (the caller's User
  document ID), `revoked=False`, and `context=API`. Returns a list of
  `TokenRecord` objects. SSE tickets and session tokens are excluded.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:api-token:read`
  """
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

@router.delete(
  "/user/{user_key}",
  response_model=APIResponse,
  responses={
    500: {"description": "Database error while archiving the user record"},
  },
  dependencies=[Depends(auth.verify_token)],
)
async def archive_user(user_key: str):
  """Soft-delete (archive) a user account.

  Sets `trash=True` on the `User` document identified by `user_key`. The
  account remains in the database for audit and traceability but is excluded
  from active user lists. Does not revoke any outstanding tokens.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `org:user:delete`
  """
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


