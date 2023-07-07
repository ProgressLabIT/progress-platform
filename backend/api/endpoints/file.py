import os
import traceback

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from models.form import FileBucket, FileTargetData
from utils.db import db
from utils.file import UserFile


router = APIRouter()

collection_map = {
  FileBucket.ISSUE: 'Issue',
  FileBucket.PRODUCT: 'Product',
  FileBucket.STEP: 'Step',
  FileBucket.USER: 'User'
}


def target_data(
  bucket: FileBucket = Form(...),
  target_key: str = Form(...)
):
  # Check whether an entity with the key provided exists
  if not db.collection(collection_map[bucket]).has(target_key):
    raise HTTPException(
      status_code = 404,
      detail = f'No {target.value} with key {target_key} exists on the database'
    )

  return FileTargetData(bucket=bucket, key=target_key)


@router.post('/file')
async def upload_files(
  contents: list[UploadFile],
  target: FileTargetData = Depends(target_data)
):

  for file in contents:
    handler = UserFile(base_path=target.bucket.value, append_path=target.key, file=file)
    try:
      await handler.write_file()
    except Exception:
      raise HTTPException(
        status_code=500,
        detail=dict(
          message=f'Could not write {file.name} file to disk',
          error=traceback.format_exc()
        )
      )


@router.delete('/file')
async def delete_files(
  filenames: list[str],
  target: FileTargetData = Depends(target_data)
):

  handler = UserFile(base_path=target.bucket.value, append_path=target.key)
  for filename in filenames:
    try:
      handler.delete_file(filename)
    except FileNotFoundError:
      raise HTTPException(
        status_code=404,
        detail=dict(
          message=f"No file named {filename} is associated with {target.bucket.value} {target.key}",
          error=traceback.format_exc()
        )
      )

  # Delete directory if empty
  if os.listdir(handler.folder_path) == []:
    os.rmdir(handler.folder_path)
