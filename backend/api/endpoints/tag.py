from fastapi import APIRouter, Depends
from utils import auth

from utils.api import APIResponse
from utils.db import db
from utils.exceptions import HTTPError
from models.tag import Tag, TagConnectionUpdate, TagAssignmentContext

router = APIRouter()

context_map = {
  TagAssignmentContext.PRODUCT.value: 'Product',
}


@router.get(
  '/tag',
  response_model=APIResponse[list[Tag]],
  responses={
    500: {"description": "Database error while fetching tags"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def get_tags(context: TagAssignmentContext | None = None, context_key: str | None = None):
  """List tags, optionally scoped to a specific entity.

  Returns all tags from the `Tag` collection when no `context` is supplied.
  When `context` and `context_key` are both provided, returns only tags
  connected to the specified entity via `has_tag` edges.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `config:tag:read`
  """
  try:
    if not context:
      cursor = db.collection('Tag').all()
    else:
      cursor = db.aql.execute(
        """
        FOR edge IN has_tag
          FILTER edge._from == @from_id
          RETURN DOCUMENT(Tag, edge._to)
        """,
        bind_vars=dict(
          from_id=f'{context_map[context]}/{context_key}',
        )
      )

    tags = [Tag(**tag) for tag in cursor]

    return APIResponse(
      message='Tags retrieved successfully',
      detail=tags
    )
  except:
    raise HTTPError(500, 'There was a problem retrieving the tags')


@router.post(
  '/tag',
  response_model=APIResponse[Tag],
  responses={
    500: {"description": "Database error during tag insertion"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def create_tag(tag: Tag):
  """Create a new tag.

  Inserts a `Tag` document into the `Tag` collection. Tags can subsequently
  be connected to entities (e.g. products) via `POST /tag/update-connections`.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `config:tag:write`
  """
  try:
    tag = db.collection('Tag').insert(tag, return_new=True)['new']

    return APIResponse(
      message='Tag created successfully',
      detail=Tag(**tag),
      status=201
    )
  except:
    raise HTTPError(500, 'There was a problem creating the tag')


@router.post(
  '/tag/update-connections',
  response_model=APIResponse[None],
  responses={
    500: {"description": "Transaction error while applying tag connection changes"},
  },
  dependencies=[Depends(auth.verify_token)],
)
def connect_tags(connection_updates: list[TagConnectionUpdate]):
  """Add or remove tag connections for one or more entities.

  Accepts a list of `TagConnectionUpdate` objects each specifying a `type`
  (`add` or `remove`), a `tag_key`, a `context` (e.g. `product`), and a
  `context_key`. All changes are applied within a single ArangoDB transaction
  against the `has_tag` edge collection.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `config:tag:write`
  """
  try:
    tx = db.begin_transaction(write=['has_tag'])

    to_add = []
    to_remove = []
    for update in connection_updates:
      connection = dict(_from=f'{context_map[update.context]}/{update.context_key}', _to=f'Tag/{update.tag_key}')
      if update.type == 'add':
        to_add.append(connection)
      elif update.type == 'remove':
        to_remove.append(connection)

    if to_add:
      tx.collection('has_tag').insert_many(to_add)

    if to_remove:
      tx.aql.execute(
        """
        FOR record_to_remove IN @to_remove
          FOR record IN has_tag
          FILTER
            record._from == record_to_remove._from
            && record._to == record_to_remove._to
          REMOVE record IN has_tag
        """,
        bind_vars=dict(to_remove=to_remove)
      )

    tx.commit_transaction()

    return APIResponse(
      message='Tags connected successfully',
      status=201
    )
  except:
    tx.abort_transaction()
    raise HTTPError(500, 'There was a problem connecting the tags')
