import os
import traceback

from fastapi import APIRouter, Body, Depends, Form, HTTPException, UploadFile, Depends

from commons.models.form import FileBucket, FileTargetData
from commons.utils.db import db
from utils.file import FileHandler
from utils import auth


router = APIRouter()

collection_map = {
  FileBucket.ISSUE: 'Issue',
  FileBucket.PRODUCT: 'Product',
  FileBucket.TRACEABILITY: 'WorkOrder',
  FileBucket.USER: 'User',
  FileBucket.SERIALS: 'Serial'
}


def verify_target_data(
  bucket: FileBucket,
  object_key: str,
  subfolder: str | None = None
):
  object = db.collection(collection_map[bucket]).get(object_key)
  # Check whether an entity with the key provided exists
  if not object:
    raise HTTPException(
      status_code = 404,
      detail = f'No {collection_map[bucket]} with key {object_key} exists on the database'
    )

  # Check whether the field key corresponds to an actual field (does not check whether the field is used in a specific form)
  if subfolder:
    invalid = True
    if bucket == FileBucket.ISSUE:
      for data in object['data']:
        if data['form_field_key'] == subfolder:
          invalid = False
          break
    if bucket == FileBucket.SERIALS:
      serial = db.collection('Serial').get(object_key)
      if not serial:
        raise HTTPException(
          status_code = 404,
          detail = f'No Serial with key {object_key} exists on the database'
        )
      for data in object['data']:
        if data['form_field_key'] == subfolder:
          invalid = False
          break
    elif bucket == FileBucket.TRACEABILITY:
      batch_key, step_key, custom_field_key, form_field_key = subfolder.split('/')
      batch = db.collection('Batch').get(batch_key)
      step = db.collection('Step').get(step_key)
      custom_field = db.collection('CustomField').get(custom_field_key)
      if not batch:
        raise HTTPException(
          status_code = 404,
          detail = f'No Batch with key {batch_key} exists on the database'
        )
      if not step:
        raise HTTPException(
          status_code = 404,
          detail = f'No Step with key {step_key} exists on the database'
        )
      if not custom_field:
        raise HTTPException(
          status_code = 404,
          detail = f'No CustomField with key {custom_field_key} exists on the database'
        )
      for field in step['form_fields']:
        if field['_key'] == form_field_key:
          if field['custom_field_key'] != custom_field_key:
            raise HTTPException(
              status_code = 404,
              detail = f'FormField with key {form_field_key} does not correspond to CustomField with key {custom_field_key}'
            )
          invalid = False
          break

    if invalid:
      raise HTTPException(
        status_code = 404,
        detail = f'No field with with key {subfolder} exists on the database'
      )

  return FileTargetData(bucket=bucket, object_key=object_key, subfolder=subfolder)


@router.post('/files',
    dependencies=[Depends(auth.verify_token)])
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


@router.delete('/files',
    dependencies=[Depends(auth.verify_token)])
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
