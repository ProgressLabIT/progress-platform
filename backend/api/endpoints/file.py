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
  FileBucket.TRACEABILITY: 'WorkOrder',
  FileBucket.USER: 'User'
}


def verify_target_data(
  bucket: FileBucket,
  object_key: str,
  subfolder: str | None = None
):
  target = db.collection(collection_map[bucket]).get(object_key)
  # Check whether an entity with the key provided exists
  if not target:
    raise HTTPException(
      status_code = 404,
      detail = f'No {collection_map[bucket]} with key {object_key} exists on the database'
    )

  # Check whether the field key corresponds to an actual field (does not check whether the field is used in a specific form)
  if subfolder:
    if bucket == FileBucket.ISSUE:
      form_field_keys = [f['form_field_key'] for f in target['data']]
      if subfolder not in form_field_keys:
        raise HTTPException(
          status_code = 404,
          detail = f'No form field with with key {subfolder} exists for this type of issue'
        )

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
        
    elif bucket == FileBucket.PRODUCT:
      doc_type, *rest = subfolder.split('/')
      if doc_type == 'meta':
        field_key = rest[0]
        custom_field = db.collection('CustomField').get(field_key)
        if not custom_field:
          raise HTTPException(
            status_code = 404,
            detail = f'No field with key {field_key} exists on the database'
          )
        if not custom_field.get('type', None) == 'files':
          raise HTTPException(
            status_code = 422,
            detail = f'Field {field_key} is not of file type'
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
