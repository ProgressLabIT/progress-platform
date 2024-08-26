from fastapi import APIRouter, HTTPException, UploadFile, Depends
from utils import auth
from fastapi.responses import FileResponse
from shutil import copyfileobj
from os import path
from uuid import uuid4


from utils.api import APIResponse
from commons.utils.db import db
from commons.utils.config import get_config
from utils.exceptions import HTTPError
from utils.media import delete_media as _delete_media
from models.process import Media

router = APIRouter()
media_root_path = get_config().media_path

def make_media(file: UploadFile, key: str = None):
  try:
    return Media(
      key=key or str(uuid4()),
      name=file.filename,
      size=file.size,
      content_type=file.content_type
    )
  except Exception as ex:
    raise HTTPException(
      status_code=422,
      detail=str(ex)
    )

def write_media_file(file: UploadFile, media_key: str):
  try:
    filepath = path.join(media_root_path, media_key)
    with open(filepath, 'wb') as buffer:
      copyfileobj(file.file, buffer)
  except:
    raise HTTPError(500, 'Could not write file to disk')

# TODO: If a created media is not connected to any entity in a reasonable amount of time, delete it (cron job?) (use created_at field as reference)
@router.post('/media/create',
    dependencies=[Depends(auth.verify_token)])
def create_media(file: UploadFile):
  media = make_media(file)
  write_media_file(file, media.key)

  media = db.collection('Media').insert(media.dict(by_alias=True), return_new=True)['new']

  return APIResponse(
    status_code=201,
    message='Media created successfully',
    detail=media
  )

@router.patch('/media/{media_key}',
    dependencies=[Depends(auth.verify_token)])
def update_media(media_key: str, file: UploadFile):
  media = db.collection('Media').get(media_key)
  if not media:
    raise HTTPError(404, 'Media not found')

  media = make_media(file, media_key)
  write_media_file(file, media.key)

  media = db.collection('Media').update(media.dict(by_alias=True), return_new=True)['new']

  return APIResponse(
    status_code=200,
    message='Media updated successfully',
    detail=media
  )

@router.delete('/media/{media_key}',
    dependencies=[Depends(auth.verify_token)])
def delete_media(media_key: str):
  media = db.collection('Media').has(media_key)
  if not media:
    raise HTTPException(
      status_code=404,
      detail='Media not found'
    )

  has_any_connections = db.aql.execute(
    """
    RETURN LENGTH(
      FOR mc IN 'media_connection' mc._to == CONCAT('Media/', @media_key) RETURN mc
    ) > 0
    """,
    bind_vars=dict(media_key=media_key)
  ).next()
  if has_any_connections:
    raise HTTPException(
      status_code=422,
      detail='Media is connected to one or more entities. Remove the connections first.'
    )

  try:
    return _delete_media(media_key)
  except Exception as ex:
    raise HTTPException(status_code=500, detail=str(ex))


@router.get('/media/{media_key}',
    dependencies=[Depends(auth.verify_token)])
def get_media(media_key: str):
  media = db.collection('Media').get(media_key)
  if not media:
    raise HTTPException(
      status_code=404,
      detail='Media not found'
    )

  return FileResponse(
    path=path.join(media_root_path, media_key),
    filename=media['name'],
    media_type=media['content_type']
  )
