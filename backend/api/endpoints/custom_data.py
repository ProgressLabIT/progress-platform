import re
import traceback

from fastapi import APIRouter, HTTPException, Depends, Query
from utils import auth
from utils.api import APIResponse
from models.custom_data import CustomData, KEY_PATTERN, KEY_MAX_LENGTH
from utils.db import db

router = APIRouter()

COLLECTION = 'CustomData'


def _validate_key(key: str):
    """Validate _key format. Raises 422 if invalid."""
    if not KEY_PATTERN.match(key) or len(key) > KEY_MAX_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f'Key must match {KEY_PATTERN.pattern} and be at most {KEY_MAX_LENGTH} chars',
        )


@router.get('/custom-data',
    dependencies=[Depends(auth.verify_token)])
def list_custom_data(search: str | None = None):
    query = """
        FOR d IN CustomData
        FILTER @search == null
            OR CONTAINS(LOWER(d._key), LOWER(@search))
            OR CONTAINS(LOWER(d.description || ''), LOWER(@search))
        SORT d._key
        RETURN d
    """
    cursor = db.aql.execute(query, bind_vars=dict(search=search))
    return [CustomData(**d) for d in cursor]


@router.get('/custom-data/{key}',
    dependencies=[Depends(auth.verify_token)])
def get_custom_data(key: str):
    doc = db.collection(COLLECTION).get(key)
    if not doc:
        raise HTTPException(status_code=404, detail=f'CustomData {key!r} not found')
    return CustomData(**doc)


@router.put('/custom-data/{key}',
    dependencies=[Depends(auth.verify_token)])
def upsert_custom_data(key: str, body: CustomData):
    _validate_key(key)
    doc = body.model_dump(by_alias=True, exclude_none=True)
    doc['_key'] = key

    collection = db.collection(COLLECTION)
    existing = collection.get(key)

    try:
        if existing:
            collection.replace(doc, check_rev=False)
            message = f'CustomData {key!r} updated'
        else:
            collection.insert(doc)
            message = f'CustomData {key!r} created'
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

    return APIResponse(message=message, detail=dict(_key=key))


@router.delete('/custom-data/{key}',
    dependencies=[Depends(auth.verify_token)])
def delete_custom_data(key: str):
    collection = db.collection(COLLECTION)
    if not collection.get(key):
        raise HTTPException(status_code=404, detail=f'CustomData {key!r} not found')

    try:
        collection.delete(key)
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

    return APIResponse(message=f'CustomData {key!r} deleted')
