from fastapi import APIRouter

from utils.api import APIResponse
from utils.db import db
from utils.exceptions import HTTPError
from models.tag import Tag

router = APIRouter()


@router.get('/tag', response_model=APIResponse[list[Tag]])
def get_tags():
  try:
    tags_cursor = db.collection('Tag').all()
    tags = [Tag(**tag) for tag in tags_cursor]

    return APIResponse(
      message='Tags retrieved successfully',
      detail=tags
    )
  except:
    raise HTTPError(500, 'There was a problem retrieving the tags')


@router.post('/tag', response_model=APIResponse[Tag])
def create_tag(tag: Tag):
  try:
    tag = db.collection('Tag').insert(tag, return_new=True)['new']

    return APIResponse(
      message='Tag created successfully',
      detail=Tag(**tag),
      status=201
    )
  except:
    raise HTTPError(500, 'There was a problem creating the tag')
