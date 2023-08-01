import os
import traceback

from fastapi import APIRouter, Body, Depends, Form, HTTPException, UploadFile

from models.form import FileBucket, FileTargetData
from utils.db import db
from utils.file import FileHandler


router = APIRouter()

collection_map = {
  FileBucket.ISSUE: 'Issue',
  FileBucket.PRODUCT: 'Product',
  FileBucket.STEP: 'Step',
  FileBucket.USER: 'User'
}


def verify_target_data(
  bucket: FileBucket,
  object_key: str,
  subfolder: str = None
):
  # Check whether an entity with the key provided exists
  if not db.collection(collection_map[bucket]).has(object_key):
    raise HTTPException(
      status_code = 404,
      detail = f'No {target.value} with key {object_key} exists on the database'
    )

  # Check whether the field key corresponds to an actual field (does not check whether the field is used in a specific form)
  if subfolder and not db.collection('CustomField').has(subfolder):
    raise HTTPException(
      status_code = 404,
      detail = f'No field with with key {field_key} exists on the database'
    )

  return FileTargetData(bucket=bucket, object_key=object_key, subfolder=subfolder)


@router.post('/files')
async def upload_files(
  contents: list[UploadFile],
  bucket: FileBucket = Form(...),
  object_key: str = Form(...),
  subfolder: str = Form(None),
  reset_folder: bool = Form(False),
):

  target = verify_target_data(bucket, object_key, subfolder)

  handler = FileHandler(
    bucket = target.bucket.value,
    object_key = target.object_key,
    subfolder = target.subfolder
  )

  if reset_folder:
    handler.clean_dir()

  for file in contents:
    try:
      await handler.write_file(file=file)
    except Exception:
      raise HTTPException(
        status_code=500,
        detail=dict(
          message=f'Could not write {file.name} file to disk',
          error=traceback.format_exc()
        )
      )


@router.delete('/files')
async def delete_files(
  filenames: list[str],
  bucket: FileBucket = Body(...),
  object_key: str = Body(...),
  subfolder: str = Body(None),
):

  target = verify_target_data(bucket, object_key, subfolder)

  handler = FileHandler(bucket=target.bucket.value, object_key=target.object_key, subfolder=target.subfolder)
  for filename in filenames:
    try:
      handler.delete_file(filename)
    except FileNotFoundError:
      raise HTTPException(
        status_code=404,
        detail=dict(
          message=f"No file named {filename} is associated with {target.bucket.value} {target.object_key}",
          error=traceback.format_exc()
        )
      )
